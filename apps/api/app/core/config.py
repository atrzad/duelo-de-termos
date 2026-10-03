from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# O .env fica na raiz do monorepo e é compartilhado com o frontend.
ROOT_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"

# apps/api/dados/duelo.db — arquivo local, nunca vai pro git (ver .gitignore).
DADOS_DIR = Path(__file__).resolve().parents[2] / "dados"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DADOS_DIR / 'duelo.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Duelo de Termos API"
    # Lista separada por vírgulas, ex.: "http://localhost:5173,https://maquina.tailnet.ts.net"
    cors_origins: str = "http://localhost:5173"
    database_url: str = DEFAULT_DATABASE_URL

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
