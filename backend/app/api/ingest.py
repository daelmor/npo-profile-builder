"""Ingestion endpoints: pasted text or an uploaded PDF -> structured profile."""

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import IngestionError
from app.db import get_session
from app.schemas.api import IngestTextRequest, ProfileDetail
from app.services import ingestion, profiles
from app.services.pdf import extract_pdf_text

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/text", response_model=ProfileDetail, status_code=201)
async def ingest_text(
    payload: IngestTextRequest,
    session: AsyncSession = Depends(get_session),
) -> ProfileDetail:
    result = await ingestion.ingest(
        session=session, raw_text=payload.text, filename=payload.title
    )
    return profiles.detail_from_result(result)


@router.post("/file", response_model=ProfileDetail, status_code=201)
async def ingest_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> ProfileDetail:
    data = await file.read()

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise IngestionError(
            f"File exceeds the {settings.max_upload_mb} MB limit.", status_code=413
        )

    content_type = file.content_type or ""
    filename = file.filename or "upload.pdf"
    if "pdf" not in content_type.lower() and not filename.lower().endswith(".pdf"):
        raise IngestionError("Only PDF files are supported — paste text for other formats.")

    text = extract_pdf_text(data)
    result = await ingestion.ingest(
        session=session, raw_text=text, filename=filename, content_type=content_type
    )
    return profiles.detail_from_result(result)
