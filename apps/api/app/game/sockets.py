"""Eventos Socket.IO do 1v1 (Fase 4, versão mínima: sem reconexão, sem conta
de usuário — sala por código, corrida simultânea, primeiro a acertar vence).
Eventos pequenos e tipados (regra 11 do PROJECT_SCOPE.md); todo payload de
entrada passa por validação de schema (regra 6) antes de tocar no domínio.
"""

from typing import Any

import socketio
from pydantic import ValidationError

from app.game.rooms import (
    MAX_TENTATIVAS,
    SalaEmAndamentoError,
    SalaNaoEncontradaError,
    gerenciador,
)
from app.game.schemas import CriarSalaPayload, EntrarSalaPayload, EnviarPalpitePayload

# "*" em vez de settings.cors_origin_list de propósito: em produção o
# front é servido pela própria API (mesma origem), mas em dev o Vite roda
# numa porta diferente (5173 -> 8000) e manter a lista fixa quebraria um dos
# dois cenários. Sem cookies/sessão no handshake (identidade = nome + código
# de sala), liberar a origem aqui não abre superfície de ataque nova.
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


async def _erro(sid: str, mensagem: str) -> None:
    # Regra 13: erro amigável, nunca um stack trace ou payload cru pro cliente.
    await sio.emit("erro", {"mensagem": mensagem}, to=sid)


@sio.event  # type: ignore[untyped-decorator]
async def disconnect(sid: str) -> None:
    sala = gerenciador.remover_jogador(sid)
    if sala is None:
        return
    for outro_sid in sala.jogadores:
        await sio.emit("oponente_saiu", {}, to=outro_sid)


@sio.event  # type: ignore[untyped-decorator]
async def criar_sala(sid: str, data: Any) -> None:
    try:
        payload = CriarSalaPayload.model_validate(data)
    except ValidationError:
        await _erro(sid, "Nome inválido.")
        return

    sala = gerenciador.criar_sala(sid, payload.nome)
    await sio.enter_room(sid, sala.codigo)
    await sio.emit("sala_criada", {"codigo": sala.codigo}, to=sid)


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

    for jogador_sid in sala.jogadores:
        oponente = sala.outro_jogador(jogador_sid)
        await sio.emit(
            "partida_iniciada",
            {"oponente": oponente.nome if oponente else "Oponente"},
            to=jogador_sid,
        )


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
            "tentativasRestantes": MAX_TENTATIVAS - len(jogador.tentativas),
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
        for jogador_sid in sala.jogadores:
            await sio.emit(
                "fim_de_jogo",
                {
                    "resultado": sala.resultado_para(jogador_sid),
                    "palavraSecreta": sala.palavra_secreta,
                },
                to=jogador_sid,
            )
