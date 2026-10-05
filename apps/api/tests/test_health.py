from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_allows_configured_origin() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"Origin": "http://localhost:5173"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


@pytest.fixture
def cliente_com_frontend_falso(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """`WEB_DIST` falso (não depende de `npm run build` ter rodado) pra
    testar as regras de Cache-Control do app servindo o frontend."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "assets" / "index-ABC123.js").write_text("console.log('ok')")
    (dist / "index.html").write_text("<!doctype html><html></html>")

    monkeypatch.setattr(main, "WEB_DIST", dist)
    return TestClient(create_app())


def test_index_html_nunca_e_cacheado(cliente_com_frontend_falso: TestClient) -> None:
    """Sem isso, o navegador pode guardar um index.html velho (apontando pro
    JS/CSS de um build antigo) e nunca buscar o deploy novo -- só apareceu
    testando num celular de verdade, não com TestClient (ver 2026-10-04)."""
    response = cliente_com_frontend_falso.get("/jogo")

    assert response.headers["cache-control"] == "no-cache"


def test_assets_com_hash_tem_cache_longo(cliente_com_frontend_falso: TestClient) -> None:
    response = cliente_com_frontend_falso.get("/assets/index-ABC123.js")

    assert response.headers["cache-control"] == "public, max-age=31536000, immutable"
