from collections.abc import Awaitable, Callable
from pathlib import Path

import socketio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.game.sockets import sio

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
        # Arquivos em /assets têm hash no nome (gerado pelo Vite a cada
        # build) -- cache longo e seguro, nunca fica desatualizado porque um
        # build novo gera um nome novo. StaticFiles não tem opção nativa pra
        # header extra, daí o middleware.
        @app.middleware("http")
        async def cache_control_assets(
            request: Request, call_next: Callable[[Request], Awaitable[Response]]
        ) -> Response:
            response = await call_next(request)
            if request.url.path.startswith("/assets/"):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            return response

        app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="web-assets")

        @app.get("/{caminho:path}", include_in_schema=False)
        async def servir_frontend(caminho: str) -> FileResponse:
            # Serve o arquivo real se existir (ex: favicon.ico); senão cai no
            # index.html pra o React Router cuidar da rota (SPA).
            # resolve() + is_relative_to() impede path traversal via "..".
            # Cache-Control: no-cache em TUDO aqui (nunca o /assets com hash
            # acima) -- sem isso o navegador pode guardar um index.html velho
            # e nunca buscar o JS/CSS novo depois de um deploy (ele só reage
            # ao <script src> com hash NOVO que está dentro do index.html
            # novo, então o index.html precisa sempre revalidar).
            candidato = (WEB_DIST / caminho).resolve()
            headers = {"Cache-Control": "no-cache"}
            if caminho and candidato.is_relative_to(WEB_DIST) and candidato.is_file():
                return FileResponse(candidato, headers=headers)
            return FileResponse(WEB_DIST / "index.html", headers=headers)

    return app


app = create_app()

# uvicorn serve este, não `app` direto: envolve a FastAPI com o servidor
# Socket.IO (monta em /socket.io, delega todo o resto pra `app`).
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
