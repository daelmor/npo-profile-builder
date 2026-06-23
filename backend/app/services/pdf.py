"""PDF text extraction (pypdf), with graceful failure for bad inputs."""

import io

from pypdf import PdfReader

from app.core.errors import IngestionError


def extract_pdf_text(data: bytes) -> str:
    """Extract text from PDF bytes. Raises IngestionError on unreadable input."""
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # pypdf raises a variety of types on bad PDFs
        raise IngestionError(
            "The PDF could not be read — it may be corrupt or password-protected."
        ) from exc

    text = "\n\n".join(pages).strip()
    if not text:
        raise IngestionError(
            "No extractable text found in the PDF (it may be a scan of images, "
            "which this MVP does not OCR)."
        )
    return text
