# Ganymede API — Document Parsing Service

"""Parse documents and extract text with provenance."""

import hashlib
import os
from dataclasses import dataclass
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


@dataclass
class PageResult:
    """A parsed page with provenance."""
    page_number: int
    text: str
    start_offset: int
    end_offset: int
    parser_version: str


@dataclass
class ParseResult:
    """Result of parsing a document."""
    pages: list[PageResult]
    sha256: str
    page_count: int
    parser_version: str
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None


def compute_sha256(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def _validate_not_empty(page_count: int, parser_name: str):
    """Validate that a document has at least one page."""
    if page_count == 0:
        raise ValueError(
            f"{parser_name} produced 0 pages — file may be corrupt, empty, or password-protected"
        )


def parse_pdf(file_bytes: bytes) -> ParseResult:
    """Parse a PDF file using PyMuPDF."""
    import fitz  # PyMuPDF

    parser_version = settings.PYMUPDF_PARSER_VERSION
    sha256 = compute_sha256(file_bytes)

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {e}")

    pages = []
    global_offset = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        start_offset = global_offset
        end_offset = global_offset + len(text)
        global_offset = end_offset + 1  # +1 for page separator

        pages.append(PageResult(
            page_number=page_num + 1,
            text=text,
            start_offset=start_offset,
            end_offset=end_offset,
            parser_version=parser_version,
        ))

    page_count = len(doc)
    doc.close()

    _validate_not_empty(page_count, "PyMuPDF")

    return ParseResult(
        pages=pages,
        sha256=sha256,
        page_count=page_count,
        parser_version=parser_version,
    )


def parse_docx(file_bytes: bytes) -> ParseResult:
    """Parse a DOCX file using python-docx."""
    import docx
    import io

    parser_version = settings.PYTHON_DOCX_PARSER_VERSION
    sha256 = compute_sha256(file_bytes)

    try:
        doc = docx.Document(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Failed to open DOCX: {e}")

    pages = []
    global_offset = 0

    # DOCX doesn't have fixed pages; treat each paragraph group as a "page"
    # For provenance, we use page 1 for the entire document
    full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])

    pages.append(PageResult(
        page_number=1,
        text=full_text,
        start_offset=0,
        end_offset=len(full_text),
        parser_version=parser_version,
    ))

    return ParseResult(
        pages=pages,
        sha256=sha256,
        page_count=1,
        parser_version=parser_version,
    )


def parse_txt(file_bytes: bytes) -> ParseResult:
    """Parse a plain text file."""
    sha256 = compute_sha256(file_bytes)
    text = file_bytes.decode("utf-8", errors="replace")

    pages = [PageResult(
        page_number=1,
        text=text,
        start_offset=0,
        end_offset=len(text),
        parser_version="txt-1.0.0",
    )]

    return ParseResult(
        pages=pages,
        sha256=sha256,
        page_count=1,
        parser_version="txt-1.0.0",
    )


def parse_scanned_pdf(file_bytes: bytes) -> ParseResult:
    """Parse a scanned PDF using OCR (Tesseract via pytesseract)."""
    import fitz
    from PIL import Image
    import pytesseract
    import io

    parser_version = f"ocr-tesseract-{settings.TESSERACT_OCR_VERSION}"
    sha256 = compute_sha256(file_bytes)

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Failed to open PDF for OCR: {e}")

    pages = []
    global_offset = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render page to image
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # OCR the image
        text = pytesseract.image_to_string(img)

        start_offset = global_offset
        end_offset = global_offset + len(text)
        global_offset = end_offset + 1

        pages.append(PageResult(
            page_number=page_num + 1,
            text=text,
            start_offset=start_offset,
            end_offset=end_offset,
            parser_version=parser_version,
        ))

    page_count = len(doc)
    doc.close()

    _validate_not_empty(page_count, "OCR")

    return ParseResult(
        pages=pages,
        sha256=sha256,
        page_count=page_count,
        parser_version=parser_version,
    )


def route_and_parse(file_bytes: bytes, mime_type: str) -> ParseResult:
    """Route file to appropriate parser based on MIME type."""
    if mime_type == "application/pdf":
        # Check if PDF is scanned (image-only)
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        has_text = False
        for page in doc:
            if page.get_text().strip():
                has_text = True
                break
        doc.close()

        if has_text:
            return parse_pdf(file_bytes)
        else:
            return parse_scanned_pdf(file_bytes)

    elif mime_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return parse_docx(file_bytes)

    elif mime_type == "text/plain":
        return parse_txt(file_bytes)

    else:
        raise ValueError(f"Unsupported MIME type: {mime_type}")
