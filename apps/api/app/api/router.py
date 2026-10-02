from fastapi import APIRouter

from app.api import health

api_router = APIRouter()
api_router.include_router(health.router)

# As rotas versionadas (/api/v1/rooms, /api/v1/matches, ...) entram aqui nas próximas fases.
