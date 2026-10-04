"""Teste de ponta a ponta do 1v1: sobe o servidor ASGI real numa porta de
teste e conecta dois clientes Socket.IO de verdade (não mocka nada da camada
de eventos, nem os timers — os testes de modo Hardcore/Normal usam durações
curtas via monkeypatch, mas é o `asyncio.sleep` de verdade rodando). Só o
pico na palavra secreta via `gerenciador` é "trapaça branca" deliberada —
mesmo processo de teste, acesso que nenhum cliente real tem — pra não
depender de sorte pra testar vitória/derrota.

O banco é trocado por um SQLite em memória via monkeypatch em
`app.game.sockets.SessionLocal`, pra não escrever no `dados/duelo.db` real.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
import socketio
import uvicorn
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.db import Base
from app.game import sockets as sockets_module
from app.game.rooms import gerenciador
from app.main import socket_app

PORTA_TESTE = 8099
URL_TESTE = f"http://127.0.0.1:{PORTA_TESTE}"


@pytest_asyncio.fixture
async def servidor_de_teste(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    engine_teste = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine_teste.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_local_teste = async_sessionmaker(engine_teste, expire_on_commit=False)
    monkeypatch.setattr(sockets_module, "SessionLocal", session_local_teste)

    config = uvicorn.Config(socket_app, host="127.0.0.1", port=PORTA_TESTE, log_level="warning")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())

    while not server.started:
        await asyncio.sleep(0.02)

    yield

    server.should_exit = True
    await task
    await engine_teste.dispose()


class ClienteDeTeste:
    def __init__(self) -> None:
        self.sio = socketio.AsyncClient()
        self.eventos: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()
        for nome_evento in (
            "sala_criada",
            "aguardando_oponente",
            "partida_iniciada",
            "resultado_palpite",
            "oponente_jogou",
            "tempo_esgotado",
            "fim_de_jogo",
            "oponente_saiu",
            "oponente_desconectado_temporariamente",
            "oponente_reconectou",
            "reconectado",
            "revanche_pedida",
            "erro",
        ):
            self.sio.on(nome_evento, self._handler(nome_evento))

    def _handler(self, nome_evento: str):  # type: ignore[no-untyped-def]
        async def handler(dados: Any = None) -> None:
            await self.eventos.put((nome_evento, dados))

        return handler

    async def conectar(self) -> None:
        await self.sio.connect(URL_TESTE)

    async def desconectar(self) -> None:
        if self.sio.connected:
            await self.sio.disconnect()

    async def proximo_evento(self, timeout: float = 2.0) -> tuple[str, Any]:
        return await asyncio.wait_for(self.eventos.get(), timeout=timeout)

    async def aguardar(self, nome_evento: str, timeout: float = 5.0) -> Any:
        """Descarta eventos até achar o esperado (útil quando a ordem entre
        tipos de evento diferentes não é garantida, ex: oponente_jogou vs
        tempo_esgotado chegando quase juntos)."""
        async with asyncio.timeout(timeout):
            while True:
                evento, dados = await self.proximo_evento(timeout)
                if evento == nome_evento:
                    return dados


@pytest.mark.asyncio
async def test_duelo_competitivo_ate_vitoria_sem_vazar_letras_do_oponente(
    servidor_de_teste: None,
) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "competitivo"})
        evento, dados = await ana.proximo_evento()
        assert evento == "sala_criada"
        assert dados["modo"] == "competitivo"
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})

        evento_ana, dados_ana = await ana.proximo_evento()
        evento_beto, dados_beto = await beto.proximo_evento()
        assert evento_ana == "partida_iniciada"
        assert dados_ana["duracaoSegundos"] is None  # Competitivo não tem timer
        assert evento_beto == "partida_iniciada"
        assert dados_beto["oponente"] == "Ana"

        # Nota: client.sio.sid é o sid do Engine.IO; o `sid` que os handlers do
        # servidor recebem é um sid de nível Socket.IO (valor diferente). Por
        # isso buscamos a sala pelo código, não pelo sid do cliente.
        sala = gerenciador._salas.get(codigo)
        assert sala is not None
        segredo = sala.palavra_secreta
        assert segredo is not None

        await ana.sio.emit("enviar_palpite", {"palavra": segredo})

        evento, dados = await ana.proximo_evento()
        assert evento == "resultado_palpite"
        assert dados["estados"] == ["correct"] * 5
        assert dados["numeroTentativa"] == 1

        evento, dados = await beto.proximo_evento()
        assert evento == "oponente_jogou"
        assert dados == {"tentativasUsadas": 1}  # nunca letras/estados do oponente

        # Competitivo: Ana venceu, mas Beto AINDA PODE jogar — diferente do
        # Hardcore, onde o primeiro acerto encerraria tudo na hora. Espera
        # entre os palpites pra respeitar o rate limit do servidor (0.3s) —
        # um cliente real nunca digita uma palavra de 5 letras mais rápido
        # que isso de qualquer forma.
        errado = "CARRO" if segredo != "CARRO" else "LIVRO"  # precisa existir no dicionario
        for _ in range(6):
            await beto.sio.emit("enviar_palpite", {"palavra": errado})
            await beto.proximo_evento()  # resultado_palpite
            await asyncio.sleep(0.35)

        dados_fim_ana = await ana.aguardar("fim_de_jogo")
        dados_fim_beto = await beto.aguardar("fim_de_jogo")
        assert dados_fim_ana["resultado"] == "venceu"
        assert dados_fim_ana["meusPontos"] == 6  # acertou na 1ª tentativa
        assert dados_fim_beto["resultado"] == "perdeu"
        assert dados_fim_beto["meusPontos"] == 0  # esgotou as 6 sem acertar
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_duelo_infinito_avanca_rodada_e_acumula_placar_sem_terminar(
    servidor_de_teste: None,
) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "infinito"})
        _, dados = await ana.proximo_evento()
        assert dados["modo"] == "infinito"
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        dados_ana_inicio = await ana.aguardar("partida_iniciada")
        dados_beto_inicio = await beto.aguardar("partida_iniciada")
        assert dados_ana_inicio["duracaoSegundos"] is None  # Infinito não tem timer
        assert dados_ana_inicio["rodada"] == 1
        assert dados_ana_inicio["meuTotal"] == 0
        assert dados_beto_inicio["totalOponente"] == 0

        sala = gerenciador._salas.get(codigo)
        assert sala is not None
        segredo = sala.palavra_secreta
        assert segredo is not None
        errado = "CARRO" if segredo != "CARRO" else "LIVRO"  # precisa existir no dicionario

        await ana.sio.emit("enviar_palpite", {"palavra": segredo})
        await ana.aguardar("resultado_palpite")  # Ana acerta de primeira: 6 pontos

        for _ in range(5):
            await beto.sio.emit("enviar_palpite", {"palavra": errado})
            await beto.aguardar("resultado_palpite")
            await asyncio.sleep(0.35)

        # 6ª tentativa de Beto fecha a rodada 1 -> servidor sorteia outra
        # palavra e reemite partida_iniciada pros dois, com o placar somado.
        await beto.sio.emit("enviar_palpite", {"palavra": errado})
        dados_ana_rodada2 = await ana.aguardar("partida_iniciada")
        dados_beto_rodada2 = await beto.aguardar("partida_iniciada")

        assert dados_ana_rodada2["rodada"] == 2
        assert dados_ana_rodada2["meuTotal"] == 6
        assert dados_ana_rodada2["totalOponente"] == 0
        assert dados_beto_rodada2["rodada"] == 2
        assert dados_beto_rodada2["meuTotal"] == 0
        assert dados_beto_rodada2["totalOponente"] == 6

        # A sala continua "jogando" pra sempre (até alguém sair) -- nenhum
        # fim_de_jogo foi emitido pra essa rodada.
        sala_depois = gerenciador._salas.get(codigo)
        assert sala_depois is not None
        assert sala_depois.status == "jogando"

        # Jogar a segunda rodada: palavra nova, tentativas zeradas.
        segredo2 = sala_depois.palavra_secreta
        assert segredo2 is not None
        await ana.sio.emit("enviar_palpite", {"palavra": segredo2})
        dados_resultado = await ana.aguardar("resultado_palpite")
        assert dados_resultado["numeroTentativa"] == 1  # não é a 7ª, é a 1ª da rodada 2
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_duelo_hardcore_primeiro_acerto_vence_na_hora(servidor_de_teste: None) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "hardcore"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        dados_ana_inicio = await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")
        assert dados_ana_inicio["duracaoSegundos"] == 90

        sala = gerenciador._salas.get(codigo)
        assert sala is not None and sala.palavra_secreta is not None
        segredo = sala.palavra_secreta

        await ana.sio.emit("enviar_palpite", {"palavra": segredo})

        fim_ana = await ana.aguardar("fim_de_jogo")
        fim_beto = await beto.aguardar("fim_de_jogo")
        assert fim_ana["resultado"] == "venceu"
        assert fim_ana["meusPontos"] == 3
        assert fim_beto["resultado"] == "perdeu"
        assert fim_beto["meusPontos"] == 0
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_revanche_direta_reinicia_a_mesma_sala(servidor_de_teste: None) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "hardcore"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")

        sala = gerenciador._salas.get(codigo)
        assert sala is not None and sala.palavra_secreta is not None
        segredo_rodada_1 = sala.palavra_secreta

        await ana.sio.emit("enviar_palpite", {"palavra": segredo_rodada_1})
        await ana.aguardar("fim_de_jogo")
        await beto.aguardar("fim_de_jogo")

        # Ana pede revanche primeiro -- Beto ainda não pediu, então a sala
        # continua "finalizada" e só o Beto é avisado do pedido.
        await ana.sio.emit("pedir_revanche", {})
        dados_pedido = await beto.aguardar("revanche_pedida")
        assert dados_pedido == {}
        assert sala.status == "finalizada"

        # Beto aceita (pede também) -- os dois recebem partida_iniciada de
        # novo, na MESMA sala.
        await beto.sio.emit("pedir_revanche", {})
        dados_ana_2 = await ana.aguardar("partida_iniciada")
        dados_beto_2 = await beto.aguardar("partida_iniciada")
        assert dados_ana_2["codigo"] == codigo
        assert dados_beto_2["codigo"] == codigo

        sala_rodada_2 = gerenciador._salas.get(codigo)
        assert sala_rodada_2 is not None
        assert sala_rodada_2.status == "jogando"

        # Jogável de verdade: manda um palpite na rodada nova (espera o
        # cooldown do rate limit -- o último palpite da Ana foi há pouco).
        assert sala_rodada_2.palavra_secreta is not None
        await asyncio.sleep(0.35)
        await ana.sio.emit("enviar_palpite", {"palavra": sala_rodada_2.palavra_secreta})
        dados_fim_ana_2 = await ana.aguardar("fim_de_jogo")
        assert dados_fim_ana_2["resultado"] == "venceu"
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_duelo_hardcore_tempo_esgota_sem_vencedor(
    servidor_de_teste: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sockets_module, "TIMER_HARDCORE_SEGUNDOS", 1)

    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "hardcore"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")

        # Ninguém envia palpite nenhum — só espera o timer (1s) estourar de verdade.
        await ana.aguardar("tempo_esgotado", timeout=3)

        fim_ana = await ana.aguardar("fim_de_jogo", timeout=3)
        fim_beto = await beto.aguardar("fim_de_jogo", timeout=3)
        assert fim_ana["resultado"] == "empate"
        assert fim_ana["meusPontos"] == 0
        assert fim_beto["meusPontos"] == 0
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_duelo_normal_prorrogacao_e_tentativa_final_de_verdade(
    servidor_de_teste: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sockets_module, "TIMER_NORMAL_SEGUNDOS", 1)
    monkeypatch.setattr(sockets_module, "TIMER_TENTATIVA_FINAL_SEGUNDOS", 1)

    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "normal"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")

        sala = gerenciador._salas.get(codigo)
        assert sala is not None and sala.palavra_secreta is not None
        segredo = sala.palavra_secreta

        # Deixa o tempo (1s) estourar sem ninguém jogar -> entra na janela
        # de tentativa final de verdade, via o timer real do servidor.
        await ana.aguardar("tempo_esgotado", timeout=3)
        await beto.aguardar("tempo_esgotado", timeout=3)

        # Ana usa a tentativa final e acerta.
        await ana.sio.emit("enviar_palpite", {"palavra": segredo})
        resultado_ana = await ana.aguardar("resultado_palpite")
        assert resultado_ana["estados"] == ["correct"] * 5

        # Beto não faz nada -> o timeout de segurança (1s) força o fim da
        # partida pra ele sozinho, sem precisar enviar palpite nenhum.
        fim_beto = await beto.aguardar("fim_de_jogo", timeout=3)
        fim_ana = await ana.aguardar("fim_de_jogo", timeout=3)

        assert fim_ana["resultado"] == "venceu"
        assert fim_ana["meusPontos"] >= 1  # categoria "tentativa_final" (+bônus de primeiro)
        assert fim_beto["resultado"] == "perdeu"
        assert fim_beto["meusPontos"] == 0

        # Falha explícita se o palpite do Beto (que nunca chegou a jogar)
        # tivesse vazado pra Ana de algum jeito.
        assert "letras" not in fim_ana
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_rate_limit_bloqueia_palpites_em_sequencia_rapida_demais(
    servidor_de_teste: None,
) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "competitivo"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")

        sala = gerenciador._salas.get(codigo)
        assert sala is not None and sala.palavra_secreta is not None
        # Precisa ser uma palavra errada (nunca a secreta) que EXISTA no
        # dicionário -- se ganhasse de primeira, as próximas tentativas
        # seriam bloqueadas por SalaEmAndamentoError, não pelo rate limit.
        errado = "CARRO" if sala.palavra_secreta != "CARRO" else "LIVRO"

        await ana.sio.emit("enviar_palpite", {"palavra": errado})
        await ana.aguardar("resultado_palpite")

        # Manda outro palpite na sequência, sem esperar o cooldown (0.3s).
        await ana.sio.emit("enviar_palpite", {"palavra": errado})
        evento, dados_erro = await ana.proximo_evento()
        assert evento == "erro"
        assert "mensagem" in dados_erro

        # Depois de esperar o cooldown passar, volta a funcionar normalmente.
        await asyncio.sleep(0.35)
        await ana.sio.emit("enviar_palpite", {"palavra": errado})
        evento, _ = await ana.proximo_evento()
        assert evento == "resultado_palpite"
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_palpite_invalido_retorna_erro_amigavel(servidor_de_teste: None) -> None:
    cliente = ClienteDeTeste()
    try:
        await cliente.conectar()
        await cliente.sio.emit("criar_sala", {"nome": "Ana", "modo": "competitivo"})
        await cliente.proximo_evento()  # sala_criada

        await cliente.sio.emit("enviar_palpite", {"palavra": "AB"})

        evento, dados = await cliente.proximo_evento()
        assert evento == "erro"
        assert "mensagem" in dados
    finally:
        await cliente.desconectar()


@pytest.mark.asyncio
async def test_palavra_que_nao_existe_e_rejeitada_sem_consumir_tentativa(
    servidor_de_teste: None,
) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "competitivo"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")

        sala = gerenciador._salas.get(codigo)
        assert sala is not None and sala.palavra_secreta is not None
        errado = "CARRO" if sala.palavra_secreta != "CARRO" else "LIVRO"

        # "ZZZZZ" tem 5 letras (passa o schema), mas não existe no dicionário.
        await ana.sio.emit("enviar_palpite", {"palavra": "ZZZZZ"})
        evento, dados_erro = await ana.proximo_evento()
        assert evento == "erro"
        assert "mensagem" in dados_erro

        # Não consumiu a tentativa -- um palpite de verdade ainda é a 1ª.
        # Espera o cooldown do rate limit (0.3s) entre os dois envios.
        await asyncio.sleep(0.35)
        await ana.sio.emit("enviar_palpite", {"palavra": errado})
        dados_resultado = await ana.aguardar("resultado_palpite")
        assert dados_resultado["numeroTentativa"] == 1
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_criar_sala_com_modo_invalido_retorna_erro(servidor_de_teste: None) -> None:
    cliente = ClienteDeTeste()
    try:
        await cliente.conectar()
        await cliente.sio.emit("criar_sala", {"nome": "Ana", "modo": "turbo"})

        evento, dados = await cliente.proximo_evento()
        assert evento == "erro"
        assert "mensagem" in dados
    finally:
        await cliente.desconectar()


@pytest.mark.asyncio
async def test_entrar_em_sala_inexistente_retorna_erro(servidor_de_teste: None) -> None:
    cliente = ClienteDeTeste()
    try:
        await cliente.conectar()
        await cliente.sio.emit("entrar_sala", {"nome": "Ana", "codigo": "ZZZZ"})

        evento, dados = await cliente.proximo_evento()
        assert evento == "erro"
        assert "mensagem" in dados
    finally:
        await cliente.desconectar()


@pytest.mark.asyncio
async def test_desconexao_avisa_o_oponente(servidor_de_teste: None) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "competitivo"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.proximo_evento()  # partida_iniciada (ana)
        await beto.proximo_evento()  # partida_iniciada (beto)

        await ana.sio.disconnect()

        # Partida "jogando": não é abandono na hora -- abre uma janela de
        # reconexão (seção 14 do PROJECT_SCOPE.md). oponente_saiu só depois
        # que a janela esgotar sem a Ana voltar (ver teste à parte, com
        # timeout curto via monkeypatch).
        evento, _ = await beto.proximo_evento()
        assert evento == "oponente_desconectado_temporariamente"
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_reconexao_recupera_o_estado_e_avisa_o_oponente(
    servidor_de_teste: None,
) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "competitivo"})
        _, dados_sala = await ana.proximo_evento()
        codigo = dados_sala["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        dados_ana_inicio = await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")
        token_ana = dados_ana_inicio["meuToken"]

        sala = gerenciador._salas.get(codigo)
        assert sala is not None
        segredo = sala.palavra_secreta
        assert segredo is not None
        errado = "CARRO" if segredo != "CARRO" else "LIVRO"  # precisa existir no dicionario

        await ana.sio.emit("enviar_palpite", {"palavra": errado})
        await ana.aguardar("resultado_palpite")
        await beto.aguardar("oponente_jogou")

        await ana.sio.disconnect()
        await beto.aguardar("oponente_desconectado_temporariamente")

        # Reconecta com um socket NOVO (sid novo), mas o mesmo token.
        await ana.sio.connect(URL_TESTE)
        await ana.sio.emit("reconectar", {"token": token_ana})

        dados_reconexao = await ana.aguardar("reconectado")
        assert dados_reconexao["oponente"] == "Beto"
        assert dados_reconexao["modo"] == "competitivo"
        assert len(dados_reconexao["minhasTentativas"]) == 1
        assert dados_reconexao["minhasTentativas"][0]["letras"] == list(errado)
        assert dados_reconexao["euConclui"] is False

        await beto.aguardar("oponente_reconectou")

        # A sessão continua jogável depois de reconectar.
        await ana.sio.emit("enviar_palpite", {"palavra": errado})
        dados_resultado = await ana.aguardar("resultado_palpite")
        assert dados_resultado["numeroTentativa"] == 2
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_token_invalido_na_reconexao_da_erro(servidor_de_teste: None) -> None:
    ana = ClienteDeTeste()
    try:
        await ana.conectar()
        await ana.sio.emit("reconectar", {"token": "token-que-nao-existe"})

        evento, dados = await ana.proximo_evento()
        assert evento == "erro"
        assert "mensagem" in dados
    finally:
        await ana.desconectar()


@pytest.mark.asyncio
async def test_sem_reconectar_a_tempo_oponente_saiu_de_verdade(
    servidor_de_teste: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sockets_module, "TIMER_RECONEXAO_SEGUNDOS", 1)

    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana", "modo": "competitivo"})
        _, dados_sala = await ana.proximo_evento()
        codigo = dados_sala["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.aguardar("partida_iniciada")
        await beto.aguardar("partida_iniciada")

        await ana.sio.disconnect()
        await beto.aguardar("oponente_desconectado_temporariamente")

        # Não reconecta -- espera a janela (1s, monkeypatchada) esgotar.
        dados_saiu = await beto.aguardar("oponente_saiu", timeout=3.0)
        assert dados_saiu == {}
    finally:
        await ana.desconectar()
        await beto.desconectar()
