"""Eventos Socket.IO do 1v1 (sala por código, 3 modos — seção 9 do
PROJECT_SCOPE.md). Eventos pequenos e tipados (regra 11); todo payload de
entrada passa por validação de schema (regra 6) antes de tocar no domínio.
"""

import asyncio
import logging
import time
from typing import Any

import socketio
from pydantic import ValidationError

from app.core.db import SessionLocal
from app.game.modes import TIMER_HARDCORE_SEGUNDOS, TIMER_NORMAL_SEGUNDOS, GameMode
from app.game.persistence import salvar_partida
from app.game.rate_limit import LimitadorDeTaxa
from app.game.rooms import (
    Sala,
    SalaEmAndamentoError,
    SalaNaoEncontradaError,
    gerenciador,
)
from app.game.schemas import (
    CriarSalaPayload,
    EntrarSalaPayload,
    EnviarPalpitePayload,
    ReconectarPayload,
)

logger = logging.getLogger(__name__)

TIMER_TENTATIVA_FINAL_SEGUNDOS = 20
# Seção 14 do PROJECT_SCOPE.md: até 30s de janela pra reconexão antes de
# tratar a saída como abandono definitivo.
TIMER_RECONEXAO_SEGUNDOS = 30

# Regra 9.1 do PROJECT_SCOPE.md: rate limit pra evitar spam de palpites.
# Aplicado também em criar_sala pra não deixar alguém flodar o servidor de
# salas vazias.
limitador_palpites = LimitadorDeTaxa(intervalo_minimo_segundos=0.3)
limitador_criar_sala = LimitadorDeTaxa(intervalo_minimo_segundos=2.0)

# "*" em vez de settings.cors_origin_list de propósito: em produção o front é
# servido pela própria API (mesma origem), mas em dev o Vite roda numa porta
# diferente (5173 -> 8000) e manter a lista fixa quebraria um dos dois
# cenários. Sem cookies/sessão no handshake (identidade = nome + código de
# sala), liberar a origem aqui não abre superfície de ataque nova.
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Timer (principal ou de tentativa final) pendente de cada sala, pra poder
# cancelar se a partida acabar antes do tempo estourar.
_timers: dict[str, asyncio.Task[None]] = {}

# Timeout de reconexão pendente, indexado pelo sid ANTIGO (o que caiu) — se
# reconectar() chegar primeiro, cancela; se o tempo acabar primeiro, vira
# abandono definitivo (ver _timeout_reconexao).
_timers_reconexao: dict[str, asyncio.Task[None]] = {}


def _cancelar_timer(codigo: str) -> None:
    task = _timers.pop(codigo, None)
    # task is not asyncio.current_task(): _finalizar_e_notificar pode ser
    # chamada DE DENTRO do próprio _timer_principal (ex: Hardcore que
    # termina por timeout) — cancelar a própria task em execução abortaria
    # o resto da função (incluindo o emit de fim_de_jogo) no meio do caminho.
    if task is not None and not task.done() and task is not asyncio.current_task():
        task.cancel()


async def _erro(sid: str, mensagem: str) -> None:
    # Regra 13: erro amigável, nunca um stack trace ou payload cru pro cliente.
    await sio.emit("erro", {"mensagem": mensagem}, to=sid)


async def _finalizar_e_notificar(sala: Sala) -> None:
    _cancelar_timer(sala.codigo)

    try:
        async with SessionLocal() as db:
            await salvar_partida(db, sala)
    except Exception:
        # Falha ao persistir não pode derrubar a notificação aos jogadores.
        logger.exception("Erro ao salvar histórico da partida %s", sala.codigo)

    for jogador_sid, jogador in sala.jogadores.items():
        oponente = sala.outro_jogador(jogador_sid)
        await sio.emit(
            "fim_de_jogo",
            {
                "resultado": sala.resultado_para(jogador_sid),
                "palavraSecreta": sala.palavra_secreta,
                "meusPontos": jogador.pontos,
                "pontosOponente": oponente.pontos if oponente else 0,
            },
            to=jogador_sid,
        )


async def _timer_principal(codigo: str, duracao: int) -> None:
    await asyncio.sleep(duracao)

    sala = gerenciador.expirar_tempo(codigo)
    if sala is None:
        return

    await sio.emit("tempo_esgotado", {}, room=codigo)

    if sala.status == "finalizada":
        await _finalizar_e_notificar(sala)
    else:
        # Modo Normal: ainda falta alguém usar a tentativa final. Timeout de
        # segurança pra sala não ficar esperando pra sempre.
        _timers[codigo] = asyncio.create_task(_timer_tentativa_final(codigo))


async def _timer_tentativa_final(codigo: str) -> None:
    await asyncio.sleep(TIMER_TENTATIVA_FINAL_SEGUNDOS)

    sala = gerenciador.forcar_fim_tentativa_final(codigo)
    if sala is not None and sala.status == "finalizada":
        await _finalizar_e_notificar(sala)


async def _abandonar_definitivamente(sid: str) -> None:
    """Remoção permanente de verdade (sem esperar reconexão): usada quando a
    sala nem chegou a começar, já tinha terminado, ou a janela de reconexão
    (30s) esgotou sem o jogador voltar."""
    sala = gerenciador.remover_jogador(sid)
    if sala is None:
        return
    _cancelar_timer(sala.codigo)
    for outro_sid in sala.jogadores:
        await sio.emit("oponente_saiu", {}, to=outro_sid)


async def _timeout_reconexao(sid_antigo: str) -> None:
    await asyncio.sleep(TIMER_RECONEXAO_SEGUNDOS)
    _timers_reconexao.pop(sid_antigo, None)

    sala = gerenciador.remover_se_ainda_desconectado(sid_antigo)
    if sala is None:
        return  # já reconectou (ou a sala já nem existia mais) -- no-op
    _cancelar_timer(sala.codigo)
    for outro_sid in sala.jogadores:
        await sio.emit("oponente_saiu", {}, to=outro_sid)


@sio.event  # type: ignore[untyped-decorator]
async def disconnect(sid: str) -> None:
    limitador_palpites.esquecer(sid)
    limitador_criar_sala.esquecer(sid)

    sala = gerenciador.sala_do_jogador(sid)
    if sala is None:
        return

    if sala.status != "jogando":
        # Sala esperando o 2º jogador, ou partida já terminada -- não faz
        # sentido abrir uma janela de reconexão pra nada. Remoção na hora,
        # igual era antes dessa funcionalidade existir.
        await _abandonar_definitivamente(sid)
        return

    gerenciador.marcar_desconectado(sid)
    oponente = sala.outro_jogador(sid)
    if oponente is not None:
        await sio.emit("oponente_desconectado_temporariamente", {}, to=oponente.sid)

    _timers_reconexao[sid] = asyncio.create_task(_timeout_reconexao(sid))


@sio.event  # type: ignore[untyped-decorator]
async def criar_sala(sid: str, data: Any) -> None:
    if not limitador_criar_sala.permitido(sid):
        await _erro(sid, "Calma! Espera um pouco antes de criar outra sala.")
        return

    try:
        payload = CriarSalaPayload.model_validate(data)
    except ValidationError:
        await _erro(sid, "Nome ou modo inválido.")
        return

    sala = gerenciador.criar_sala(sid, payload.nome, payload.modo)
    jogador = sala.jogadores[sid]
    await sio.enter_room(sid, sala.codigo)
    await sio.emit(
        "sala_criada",
        {"codigo": sala.codigo, "modo": sala.modo.value, "meuToken": jogador.token},
        to=sid,
    )


def _duracao_do_modo(modo: GameMode) -> int | None:
    if modo == GameMode.normal:
        return TIMER_NORMAL_SEGUNDOS
    if modo == GameMode.hardcore:
        return TIMER_HARDCORE_SEGUNDOS
    return None


def _tempo_restante(sala: Sala) -> int | None:
    """Segundos que ainda faltam no timer da sala, visto AGORA — usado na
    reconexão: o cliente que volta não pode receber a duração total de novo
    (reiniciaria o cronômetro do zero na tela dele)."""
    duracao_total = _duracao_do_modo(sala.modo)
    if duracao_total is None or sala.iniciada_em is None:
        return None
    if sala.tempo_expirado:
        return 0
    decorrido = time.time() - sala.iniciada_em
    return max(0, round(duracao_total - decorrido))


async def _emitir_partida_iniciada(sala: Sala) -> None:
    """Emitido no início da partida e, no modo Infinito, de novo a cada
    rodada nova (o cliente reusa o mesmo handler pra resetar o tabuleiro)."""
    duracao = _duracao_do_modo(sala.modo)
    for jogador_sid, jogador in sala.jogadores.items():
        oponente = sala.outro_jogador(jogador_sid)
        await sio.emit(
            "partida_iniciada",
            {
                "codigo": sala.codigo,
                "oponente": oponente.nome if oponente else "Oponente",
                "modo": sala.modo.value,
                "duracaoSegundos": duracao,
                "rodada": sala.rodada_atual,
                "meuTotal": jogador.pontos_totais,
                "totalOponente": oponente.pontos_totais if oponente else 0,
                "meuToken": jogador.token,
            },
            to=jogador_sid,
        )


@sio.event  # type: ignore[untyped-decorator]
async def entrar_sala(sid: str, data: Any) -> None:
    try:
        payload = EntrarSalaPayload.model_validate(data)
    except ValidationError:
        await _erro(sid, "Nome ou código inválido.")
        return

    try:
        sala = gerenciador.entrar_sala(sid, payload.nome, payload.codigo)
    except SalaNaoEncontradaError:
        await _erro(sid, "Sala não encontrada.")
        return
    except SalaEmAndamentoError:
        await _erro(sid, "Essa sala já está cheia ou em andamento.")
        return

    await sio.enter_room(sid, sala.codigo)

    if sala.status != "jogando":
        jogador = sala.jogadores[sid]
        await sio.emit("aguardando_oponente", {"meuToken": jogador.token}, to=sid)
        return

    await _emitir_partida_iniciada(sala)

    duracao = _duracao_do_modo(sala.modo)
    if duracao is not None:
        _timers[sala.codigo] = asyncio.create_task(_timer_principal(sala.codigo, duracao))


@sio.event  # type: ignore[untyped-decorator]
async def reconectar(sid: str, data: Any) -> None:
    """Seção 14 do PROJECT_SCOPE.md: o cliente guarda o token recebido em
    sala_criada/partida_iniciada no navegador e manda de volta aqui depois
    de uma queda de conexão, dentro da janela de TIMER_RECONEXAO_SEGUNDOS."""
    try:
        payload = ReconectarPayload.model_validate(data)
    except ValidationError:
        await _erro(sid, "Token de reconexão inválido.")
        return

    resultado = gerenciador.reconectar(payload.token, sid)
    if resultado is None:
        await _erro(sid, "Não foi possível reconectar — a sessão não existe mais.")
        return
    sala, jogador, sid_antigo = resultado

    tarefa_pendente = _timers_reconexao.pop(sid_antigo, None)
    if tarefa_pendente is not None and not tarefa_pendente.done():
        tarefa_pendente.cancel()

    await sio.enter_room(sid, sala.codigo)

    oponente = sala.outro_jogador(sid)
    await sio.emit(
        "reconectado",
        {
            "oponente": oponente.nome if oponente else "Oponente",
            "modo": sala.modo.value,
            "duracaoSegundos": _tempo_restante(sala),
            "rodada": sala.rodada_atual,
            "meuTotal": jogador.pontos_totais,
            "totalOponente": oponente.pontos_totais if oponente else 0,
            "meuToken": jogador.token,
            "minhasTentativas": [
                {"letras": t.letras, "estados": t.estados} for t in jogador.tentativas
            ],
            "tentativasOponente": len(oponente.tentativas) if oponente else 0,
            "tempoEsgotado": sala.tempo_expirado,
            "euConclui": jogador.concluido,
        },
        to=sid,
    )

    if oponente is not None:
        await sio.emit("oponente_reconectou", {}, to=oponente.sid)


@sio.event  # type: ignore[untyped-decorator]
async def enviar_palpite(sid: str, data: Any) -> None:
    if not limitador_palpites.permitido(sid):
        await _erro(sid, "Calma! Espera um pouco antes de enviar outro palpite.")
        return

    try:
        payload = EnviarPalpitePayload.model_validate(data)
    except ValidationError:
        await _erro(sid, "Palpite precisa ter 5 letras.")
        return

    try:
        sala, tentativa, numero_tentativa, rodada_avancou = gerenciador.registrar_palpite(
            sid, payload.palavra
        )
    except SalaNaoEncontradaError:
        await _erro(sid, "Você não está em nenhuma sala.")
        return
    except SalaEmAndamentoError:
        await _erro(sid, "Não é possível enviar palpite agora.")
        return

    await sio.emit(
        "resultado_palpite",
        {
            "letras": tentativa.letras,
            "estados": tentativa.estados,
            "numeroTentativa": numero_tentativa,
        },
        to=sid,
    )

    oponente = sala.outro_jogador(sid)
    if oponente is not None:
        await sio.emit(
            "oponente_jogou",
            {"tentativasUsadas": numero_tentativa},
            to=oponente.sid,
        )

    if sala.status == "finalizada":
        await _finalizar_e_notificar(sala)
    elif rodada_avancou:
        await _emitir_partida_iniciada(sala)


@sio.event  # type: ignore[untyped-decorator]
async def pedir_revanche(sid: str, data: Any = None) -> None:
    """Fora da seção 9 do PROJECT_SCOPE.md -- pedido à parte do usuário.
    Reaproveita a sala (mesmo código, mesmos dois jogadores) depois que uma
    partida termina; só avança quando os dois pedem."""
    try:
        sala, os_dois_pediram = gerenciador.pedir_revanche(sid)
    except SalaNaoEncontradaError:
        await _erro(sid, "Você não está em nenhuma sala.")
        return
    except SalaEmAndamentoError:
        await _erro(sid, "Não é possível pedir revanche agora.")
        return

    if not os_dois_pediram:
        oponente = sala.outro_jogador(sid)
        if oponente is not None:
            await sio.emit("revanche_pedida", {}, to=oponente.sid)
        return

    await _emitir_partida_iniciada(sala)
    duracao = _duracao_do_modo(sala.modo)
    if duracao is not None:
        _timers[sala.codigo] = asyncio.create_task(_timer_principal(sala.codigo, duracao))
