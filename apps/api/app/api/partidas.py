from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.game.persistence import PartidaRegistrada

router = APIRouter(tags=["partidas"])


class PartidaOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    codigo: str
    modo: str
    palavra_secreta: str
    jogador1_nome: str
    jogador2_nome: str
    jogador1_pontos: int
    jogador2_pontos: int
    vencedor_nome: str | None
    criada_em: datetime
    finalizada_em: datetime


@router.get("/partidas", response_model=list[PartidaOut])
async def listar_partidas(
    limite: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[PartidaRegistrada]:
    resultado = await db.execute(
        select(PartidaRegistrada).order_by(PartidaRegistrada.finalizada_em.desc()).limit(limite)
    )
    return list(resultado.scalars().all())
