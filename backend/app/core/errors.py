"""Domain errors and their HTTP translation.

Services raise these instead of leaking raw exceptions to clients. The handler
turns them into clean JSON responses with appropriate status codes.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base for expected, client-facing errors."""

    status_code: int = 500

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404


class IngestionError(AppError):
    """Bad/empty PDF, unreadable text, or extraction produced nothing usable."""

    status_code = 422


class LLMError(AppError):
    """The model call failed, timed out, or returned malformed output."""

    status_code = 502


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
