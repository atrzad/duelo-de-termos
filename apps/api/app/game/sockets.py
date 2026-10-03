"""Eventos Socket.IO do 1v1 (sala por código, 3 modos — seção 9 do
PROJECT_SCOPE.md). Eventos pequenos e tipados (regra 11); todo payload de
entrada passa por validação de schema (regra 6) antes de tocar no domínio.
"""

import asyncio
import logging
from typing import Any

import socketio
from pydantic import ValidationError

from app.core.db import SessionLocal
from app.game.modes import TIMER_HARDCORE_SEGUNDOS, TIMER_NORMAL_SEGUNDOS, GameMode
from app.game.persistence import salvar_partida
from app.game.rooms import (
    Sala,
    SalaEmAndamentoError,
    SalaNaoEncontradaError,
    gerenciador,
)
from app.game.schemas import CriarSalaPayload, EntrarSalaPayload, EnviarPalpitePayload

logger = logging.getLogger(__name__)

TIMER_TENTATIVA_FINAL_SEGUNDOS = 20

# "*" em vez de settings.cors_origin_list de propósito: em produção o front é
# servido pela própria API (mesma origem), mas em dev o Vite roda numa porta
# diferente (5173 -> 8000) e manter a lista fixa quebraria um dos dois
# cenários. Sem cookies/sessão no handshake (identidade = nome + código de
# sala), liberar a origem aqui não abre superfície de ataque nova.
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# Timer (principal ou de tentativa final) pendente de cada sala, pra poder
# cancelar se a partida acabar antes do tempo estourar.
_timers: dict[str, asyncio.Task[None]] = {}


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


@sio.event  # type: ignore[untyped-decorator]
async def disconnect(sid: str) -> None:
    sala = gerenciador.remover_jogador(sid)
    if sala is None:
        return
    _cancelar_timer(sala.codigo)
    for outro_sid in sala.jogadores:
        await sio.emit("oponente_saiu", {}, to=outro_sid)


@sio.event  # type: ignore[untyped-decorator]
async def criar_sala(sid: str, data: Any) -> None:
    try:
        payload = CriarSalaPayload.model_validate(data)
    except ValidationError:
        await _erro(sid, "Nome ou modo inválido.")
        return

    sala = gerenciador.criar_sala(sid, payload.nome, payload.modo)
    await sio.enter_room(sid, sala.codigo)
    await sio.emit("sala_criada", {"codigo": sala.codigo, "modo": sala.modo.value}, to=sid)


def _duracao_do_modo(modo: GameMode) -> int | None:
    if modo == GameMode.normal:
        return TIMER_NORMAL_SEGUNDOS
    if modo == GameMode.hardcore:
        return TIMER_HARDCORE_SEGUNDOS
    return None


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
        await sio.emit("aguardando_oponente", {}, to=sid)
        return

    duracao = _duracao_do_modo(sala.modo)
    for jogador_sid in sala.jogadores:
        oponente = sala.outro_jogador(jogador_sid)
        await sio.emit(
            "partida_iniciada",
            {
                "oponente": oponente.nome if oponente else "Oponente",
                "modo": sala.modo.value,
                "duracaoSegundos": duracao,
            },
            to=jogador_sid,
        )

    if duracao is not None:
        _timers[sala.codigo] = asyncio.create_task(_timer_principal(sala.codigo, duracao))


@sio.event  # type: ignore[untyped-decorator]
async def enviar_palpite(sid: str, data: Any) -> None:
    try:
        payload = EnviarPalpitePayload.model_validate(data)
    except ValidationError:
        await _erro(sid, "Palpite precisa ter 5 letras.")
        return

    try:
        sala, tentativa = gerenciador.registrar_palpite(sid, payload.palavra)
    except SalaNaoEncontradaError:
        await _erro(sid, "Você não está em nenhuma sala.")
        return
    except SalaEmAndamentoError:
        await _erro(sid, "Não é possível enviar palpite agora.")
        return

    jogador = sala.jogadores[sid]
    await sio.emit(
        "resultado_palpite",
        {
            "letras": tentativa.letras,
            "estados": tentativa.estados,
            "numeroTentativa": len(jogador.tentativas),
        },
        to=sid,
    )

    oponente = sala.outro_jogador(sid)
    if oponente is not None:
        await sio.emit(
            "oponente_jogou",
            {"tentativasUsadas": len(jogador.tentativas)},
            to=oponente.sid,
        )

    if sala.status == "finalizada":
        await _finalizar_e_notificar(sala)
