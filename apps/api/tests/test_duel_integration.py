"""Teste de ponta a ponta do 1v1: sobe o servidor ASGI real numa porta de
teste e conecta dois clientes Socket.IO de verdade (não mocka nada da camada
de eventos). Só o pico na palavra secreta via `gerenciador` é "trapaça branca"
deliberada — mesmo processo de teste, acesso que nenhum cliente real tem —
pra não depender de sorte pra testar vitória/derrota.
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
import socketio
import uvicorn

from app.game.rooms import gerenciador
from app.main import socket_app

PORTA_TESTE = 8099
URL_TESTE = f"http://127.0.0.1:{PORTA_TESTE}"


@pytest_asyncio.fixture
async def servidor_de_teste() -> AsyncIterator[None]:
    config = uvicorn.Config(socket_app, host="127.0.0.1", port=PORTA_TESTE, log_level="warning")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())

    while not server.started:
        await asyncio.sleep(0.02)

    yield

    server.should_exit = True
    await task


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
            "fim_de_jogo",
            "oponente_saiu",
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


@pytest.mark.asyncio
async def test_duelo_completo_ate_vitoria_sem_vazar_letras_do_oponente(
    servidor_de_teste: None,
) -> None:
    ana = ClienteDeTeste()
    beto = ClienteDeTeste()
    try:
        await ana.conectar()
        await beto.conectar()

        await ana.sio.emit("criar_sala", {"nome": "Ana"})
        evento, dados = await ana.proximo_evento()
        assert evento == "sala_criada"
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})

        evento_ana, _ = await ana.proximo_evento()
        evento_beto, dados_beto = await beto.proximo_evento()
        assert evento_ana == "partida_iniciada"
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
        assert dados["tentativasRestantes"] == 5

        evento, dados = await beto.proximo_evento()
        assert evento == "oponente_jogou"
        assert dados == {"tentativasUsadas": 1}  # nunca letras/estados do oponente

        evento_ana, dados_ana = await ana.proximo_evento()
        evento_beto, dados_beto = await beto.proximo_evento()
        assert evento_ana == "fim_de_jogo"
        assert dados_ana["resultado"] == "venceu"
        assert dados_ana["palavraSecreta"] == segredo
        assert evento_beto == "fim_de_jogo"
        assert dados_beto["resultado"] == "perdeu"
    finally:
        await ana.desconectar()
        await beto.desconectar()


@pytest.mark.asyncio
async def test_palpite_invalido_retorna_erro_amigavel(servidor_de_teste: None) -> None:
    cliente = ClienteDeTeste()
    try:
        await cliente.conectar()
        await cliente.sio.emit("criar_sala", {"nome": "Ana"})
        await cliente.proximo_evento()  # sala_criada

        await cliente.sio.emit("enviar_palpite", {"palavra": "AB"})

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

        await ana.sio.emit("criar_sala", {"nome": "Ana"})
        _, dados = await ana.proximo_evento()
        codigo = dados["codigo"]

        await beto.sio.emit("entrar_sala", {"nome": "Beto", "codigo": codigo})
        await ana.proximo_evento()  # partida_iniciada (ana)
        await beto.proximo_evento()  # partida_iniciada (beto)

        await ana.sio.disconnect()

        evento, _ = await beto.proximo_evento()
        assert evento == "oponente_saiu"
    finally:
        await ana.desconectar()
        await beto.desconectar()
