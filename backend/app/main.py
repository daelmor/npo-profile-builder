"""FastAPI application: router wiring, CORS, error handlers, lifespan."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.db import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    yield
    await engine.dispose()


app = FastAPI(title="Nonprofit Profile Builder", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Nonprofit Profile Builder", "status": "ok"}
