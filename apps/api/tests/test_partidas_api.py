from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.db import Base, get_db
from app.game.modes import GameMode
from app.game.persistence import salvar_partida
from app.game.rooms import GerenciadorDeSalas, Sala
from app.main import create_app


@dataclass
class ContextoDeTeste:
    client: TestClient
    session_local: async_sessionmaker[AsyncSession]


@pytest_asyncio.fixture
async def contexto() -> AsyncIterator[ContextoDeTeste]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_local = async_sessionmaker(engine, expire_on_commit=False)

    async def _get_db_de_teste() -> AsyncIterator[AsyncSession]:
        async with session_local() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = _get_db_de_teste

    yield ContextoDeTeste(client=TestClient(app), session_local=session_local)

    await engine.dispose()


def _partida_hardcore_finalizada() -> Sala:
    gerenciador = GerenciadorDeSalas()
    sala = gerenciador.criar_sala("sid-1", "Ana", GameMode.hardcore)
    gerenciador.entrar_sala("sid-2", "Beto", sala.codigo)
    assert sala.palavra_secreta is not None
    gerenciador.registrar_palpite("sid-1", sala.palavra_secreta)
    return sala


def test_lista_partidas_vazia_quando_nao_ha_historico(contexto: ContextoDeTeste) -> None:
    resposta = contexto.client.get("/partidas")

    assert resposta.status_code == 200
    assert resposta.json() == []


@pytest.mark.asyncio
async def test_lista_partida_recem_salva(contexto: ContextoDeTeste) -> None:
    sala = _partida_hardcore_finalizada()

    async with contexto.session_local() as session:
        await salvar_partida(session, sala)

    resposta = contexto.client.get("/partidas")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert len(corpo) == 1
    assert corpo[0]["codigo"] == sala.codigo
    assert corpo[0]["modo"] == "hardcore"
    assert corpo[0]["vencedor_nome"] == "Ana"
    assert corpo[0]["jogador1_pontos"] == 3
    assert corpo[0]["jogador2_pontos"] == 0


@pytest.mark.asyncio
async def test_limite_da_paginacao_e_respeitado(contexto: ContextoDeTeste) -> None:
    async with contexto.session_local() as session:
        for _ in range(3):
            await salvar_partida(session, _partida_hardcore_finalizada())

    resposta = contexto.client.get("/partidas?limite=2")

    assert resposta.status_code == 200
    assert len(resposta.json()) == 2
