from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings

# apps/web/dist — build de produção do frontend. Só existe depois de `npm run build`;
# em dev (uvicorn --reload sem build) a pasta não existe e o mount abaixo é pulado.
WEB_DIST = (Path(__file__).resolve().parent.parent.parent / "web" / "dist").resolve()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    if WEB_DIST.is_dir():
        app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="web-assets")

        @app.get("/{caminho:path}", include_in_schema=False)
        async def servir_frontend(caminho: str) -> FileResponse:
            # Serve o arquivo real se existir (ex: favicon.ico); senão cai no
            # index.html pra o React Router cuidar da rota (SPA).
            # resolve() + is_relative_to() impede path traversal via "..".
            candidato = (WEB_DIST / caminho).resolve()
            if caminho and candidato.is_relative_to(WEB_DIST) and candidato.is_file():
                return FileResponse(candidato)
            return FileResponse(WEB_DIST / "index.html")

    return app


app = create_app()
