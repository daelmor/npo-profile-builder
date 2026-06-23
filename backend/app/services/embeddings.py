"""Slice 3 — embeddings behind a swappable provider.

Anthropic has no embeddings endpoint, so this sits behind a small protocol. The
default ("local") runs fully offline via fastembed, so RAG works with only an
ANTHROPIC_API_KEY. Voyage/OpenAI providers would slot in here behind the same
interface, selected by the EMBEDDING_PROVIDER config.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from app.config import settings


class EmbeddingProvider(Protocol):
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class LocalEmbeddingProvider:
    """fastembed (ONNX) — downloads a small model on first use, then runs offline."""

    def __init__(self, model_name: str, dim: int) -> None:
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=model_name)
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float(x) for x in vector] for vector in self._model.embed(texts)]


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.lower()
    if provider == "local":
        return LocalEmbeddingProvider(settings.embedding_model, settings.embedding_dim)
    raise NotImplementedError(
        f"Embedding provider '{settings.embedding_provider}' is not implemented; "
        "use 'local' (or add a Voyage/OpenAI provider here)."
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return get_embedding_provider().embed(texts)


def embed_query(text: str) -> list[float]:
    return get_embedding_provider().embed([text])[0]
