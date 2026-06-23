"""Aggregate API router. Slice routers are wired in here as they land."""

from fastapi import APIRouter

from app.api import health

api_router = APIRouter()
api_router.include_router(health.router)
# Slice 1: ingest, profile  |  Slice 2: chat  |  Slice 3: search
