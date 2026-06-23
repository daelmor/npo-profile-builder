"""Aggregate API router. Slice routers are wired in here as they land."""

from fastapi import APIRouter

from app.api import health, ingest, profile

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ingest.router)
api_router.include_router(profile.router)
# Slice 2: chat  |  Slice 3: search
