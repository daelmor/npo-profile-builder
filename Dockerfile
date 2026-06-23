# syntax=docker/dockerfile:1

# ---- Stage 1: build the React/Vite SPA ----
FROM node:22-alpine AS frontend
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: backend runtime (also serves the built SPA) ----
FROM python:3.12-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    FASTEMBED_CACHE_PATH=/opt/fastembed_cache \
    PATH="/app/.venv/bin:$PATH"

# onnxruntime (fastembed) needs libgomp at runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# uv for fast, locked dependency installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install runtime deps (no dev group) from the lockfile — cached unless deps change.
COPY backend/pyproject.toml backend/uv.lock backend/.python-version ./
RUN uv sync --frozen --no-dev

# App code + the built SPA.
COPY backend/ ./
COPY --from=frontend /fe/dist ./static

# Bake the embedding model into the image so cold starts don't re-download it.
RUN python -c "from app.services.embeddings import get_embedding_provider; get_embedding_provider().embed(['warmup'])"

EXPOSE 8000

# Apply migrations, then serve. PATH points at the venv so alembic/uvicorn resolve.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
