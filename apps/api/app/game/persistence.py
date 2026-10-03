"""Histórico de partidas (persistência mínima, seção 17/Fase 3 do
PROJECT_SCOPE.md): grava um registro quando uma partida termina. O estado AO
VIVO de uma partida em andamento continua em memória (`rooms.py`) — refazer
isso pra sobreviver a um crash no meio de uma rodada é reconexão de sessão
(Fase 5), escopo maior, não implementado agora.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.game.rooms import Sala


class PartidaRegistrada(Base):
    __tablename__ = "partida"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    modo: Mapped[str] = mapped_column(String(20), nullable=False)
    palavra_secreta: Mapped[str] = mapped_column(String(5), nullable=False)
    jogador1_nome: Mapped[str] = mapped_column(String(24), nullable=False)
    jogador2_nome: Mapped[str] = mapped_column(String(24), nullable=False)
    jogador1_pontos: Mapped[int] = mapped_column(Integer, nullable=False)
    jogador2_pontos: Mapped[int] = mapped_column(Integer, nullable=False)
    vencedor_nome: Mapped[str | None] = mapped_column(String(24), nullable=True)
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finalizada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


async def salvar_partida(db: AsyncSession, sala: Sala) -> None:
    jogadores = list(sala.jogadores.values())
    if len(jogadores) != 2 or sala.palavra_secreta is None or sala.iniciada_em is None:
        return

    j1, j2 = jogadores
    vencedor_nome: str | None = None
    if j1.pontos > j2.pontos:
        vencedor_nome = j1.nome
    elif j2.pontos > j1.pontos:
        vencedor_nome = j2.nome

    db.add(
        PartidaRegistrada(
            codigo=sala.codigo,
            modo=sala.modo.value,
            palavra_secreta=sala.palavra_secreta,
            jogador1_nome=j1.nome,
            jogador2_nome=j2.nome,
            jogador1_pontos=j1.pontos,
            jogador2_pontos=j2.pontos,
            vencedor_nome=vencedor_nome,
            criada_em=datetime.fromtimestamp(sala.iniciada_em, tz=UTC),
        )
    )
    await db.commit()
