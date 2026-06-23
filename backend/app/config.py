"""Application configuration via pydantic-settings.

Secrets and tunables come from environment variables or the repo-root ``.env``
file (see ``.env.example``). Secrets are optional at import time so the app can
boot for health checks without keys; their presence is validated where used.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the repo root (one level above backend/). Resolve it absolutely
# so settings load regardless of the process's working directory.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- LLM (extraction + agent) ---
    anthropic_api_key: str | None = None
    llm_model: str = "anthropic:claude-haiku-4-5"
    llm_max_tokens: int = 2048

    # --- Embeddings (RAG) ---
    embedding_provider: str = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    voyage_api_key: str | None = None
    openai_api_key: str | None = None

    # --- Database ---
    database_url: str = "postgresql+asyncpg://npo:npo@localhost:5432/npo"

    # --- App ---
    cors_origins: str = "http://localhost:5173"
    max_upload_mb: int = 10
    max_input_chars: int = 60_000

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins parsed from the comma-separated env value."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
