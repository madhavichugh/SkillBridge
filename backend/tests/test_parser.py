"""
Unit tests for the resume and JD parser service.
Verifies file format validation, size checks, text extraction, and error handling.
"""

import io
import pytest
from fastapi import HTTPException
import docx

from app.services.parser_service import (
    extract_resume_text,
    validate_jd_text,
    extract_text_from_docx,
)

def test_validate_jd_text_success():
    """Validates that sufficient JD text passes without error."""
    valid_jd = "Looking for a Senior Python Developer with 4+ years experience in FastAPI and Docker."
    result = validate_jd_text(valid_jd)
    assert result == valid_jd

def test_validate_jd_text_too_short():
    """Validates that very short JD text raises a 400 HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        validate_jd_text("Short JD")
    assert exc_info.value.status_code == 400
    assert "too short" in exc_info.value.detail.lower()

def test_extract_resume_empty_file():
    """Validates that empty file bytes raise a 400 HTTPException."""
    with pytest.raises(HTTPException) as exc_info:
        extract_resume_text("resume.pdf", b"")
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()

def test_extract_resume_unsupported_extension():
    """Validates that unsupported file types (.png, .exe) are rejected."""
    with pytest.raises(HTTPException) as exc_info:
        extract_resume_text("resume.png", b"fake binary data 12345678901234567890123456789012345")
    assert exc_info.value.status_code == 400
    assert "unsupported" in exc_info.value.detail.lower()

def test_extract_docx_document():
    """Creates a real in-memory DOCX document and tests paragraph and table reading."""
    doc = docx.Document()
    doc.add_paragraph("Jane Doe - Senior Full Stack Developer")
    doc.add_paragraph("Skills: Python, React, PostgreSQL, Docker, AWS")
    
    # Add a table to test table cell extraction
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Experience: 5 years"
    table.cell(0, 1).text = "Education: B.S. in Computer Science"

    buffer = io.BytesIO()
    doc.save(buffer)
    docx_bytes = buffer.getvalue()

    extracted = extract_resume_text("resume.docx", docx_bytes)
    assert "Jane Doe" in extracted
    assert "Python, React" in extracted
    assert "5 years" in extracted
    assert "Computer Science" in extracted

def test_extract_plain_text():
    """Validates that plain text (.txt) resumes are parsed properly."""
    txt_content = "Alex Smith\nSoftware Engineer with experience in Django, SQL, and Git."
    extracted = extract_resume_text("resume.txt", txt_content.encode("utf-8"))
    assert "Alex Smith" in extracted
    assert "Django" in extracted
