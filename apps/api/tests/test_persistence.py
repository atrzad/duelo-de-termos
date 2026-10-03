import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base
from app.game.modes import GameMode
from app.game.persistence import PartidaRegistrada, salvar_partida
from app.game.rooms import GerenciadorDeSalas, Sala


@pytest_asyncio.fixture
async def db_session():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_local = async_sessionmaker(engine, expire_on_commit=False)
    async with session_local() as session:
        yield session

    await engine.dispose()


def _sala_finalizada_competitivo() -> Sala:
    gerenciador = GerenciadorDeSalas()
    sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
    assert sala.palavra_secreta is not None
    segredo = sala.palavra_secreta
    errado = "ZZZZZ" if segredo != "ZZZZZ" else "XXXXX"

    gerenciador.registrar_palpite("sid-1", segredo)
    gerenciador.registrar_palpite("sid-2", errado)
    for _ in range(5):
        gerenciador.registrar_palpite("sid-2", errado)

    return sala


@pytest.mark.asyncio
async def test_salvar_partida_grava_um_registro(db_session: AsyncSession) -> None:
    sala = _sala_finalizada_competitivo()

    await salvar_partida(db_session, sala)

    resultado = await db_session.execute(select(PartidaRegistrada))
    registros = resultado.scalars().all()

    assert len(registros) == 1
    registro = registros[0]
    assert registro.codigo == sala.codigo
    assert registro.modo == "competitivo"
    assert registro.jogador1_nome == "Ana"
    assert registro.jogador2_nome == "Beto"
    assert registro.vencedor_nome == "Ana"
    assert registro.jogador1_pontos == 6
    assert registro.jogador2_pontos == 0


@pytest.mark.asyncio
async def test_nao_salva_partida_que_nao_tem_dois_jogadores(db_session: AsyncSession) -> None:
    gerenciador = GerenciadorDeSalas()
    sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.competitivo)

    await salvar_partida(db_session, sala)

    resultado = await db_session.execute(select(PartidaRegistrada))
    assert len(resultado.scalars().all()) == 0
