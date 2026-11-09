"""
Parser service for extracting and validating text from resumes and job descriptions.
Handles PDF (via pdfplumber), DOCX (via python-docx), and plain text.
Includes friendly validation for scanned, empty, or truncated documents.
"""

import io
from typing import Tuple
from fastapi import HTTPException, status
import pdfplumber
import docx

# Minimum character count to consider a document valid and readable
MIN_TEXT_LENGTH = 30
# Maximum file size (10 MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF file using pdfplumber.
    WHAT: Opens PDF byte stream, loops through pages, and extracts character text.
    WHY: pdfplumber preserves layout and whitespace better than basic pypdf.
    """
    extracted_pages = []
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    extracted_pages.append(page_text.strip())
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read PDF file: {str(err)}. Ensure the file is not password-protected or corrupt."
        )

    res_text = "\n\n".join(extracted_pages).strip()
    return res_text

def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts text from a Microsoft Word .docx document.
    WHAT: Loads document paragraphs and table cells into text strings.
    WHY: Resumes frequently put contact details or skills in tables.
    """
    paragraphs = []
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        # 1. Read normal paragraphs
        for p in doc.paragraphs:
            clean_text = p.text.strip()
            if clean_text:
                paragraphs.append(clean_text)

        # 2. Also read text inside tables (resumes often use tables for skills/experience)
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text and cell_text not in paragraphs:
                        paragraphs.append(cell_text)

    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read DOCX file: {str(err)}. Ensure it is a valid .docx document."
        )

    res_text = "\n".join(paragraphs).strip()
    return res_text

def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    """
    Main entry point for extracting text from an uploaded resume file.
    Validates file extension, size, and readable content.
    """
    # 1. Check file size
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded resume file is empty (0 bytes)."
        )
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume file exceeds the maximum allowed size of 10 MB."
        )

    # 2. Inspect file extension
    lower_name = filename.lower()
    if lower_name.endswith(".pdf"):
        res_text = extract_text_from_pdf(file_bytes)
    elif lower_name.endswith(".docx"):
        res_text = extract_text_from_docx(file_bytes)
    elif lower_name.endswith(".txt"):
        res_text = file_bytes.decode("utf-8", errors="ignore").strip()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF (.pdf), Word (.docx), or plain text (.txt) file."
        )

    # 3. Check for readable text (detects scanned image-only PDFs)
    if len(res_text) < MIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The uploaded document contains little or no selectable text. "
                "If this is a scanned PDF image, please provide a text-based PDF or Word document."
            )
        )

    return res_text

def validate_jd_text(jd_text: str) -> str:
    """
    Validates the target Job Description (JD) text input.
    Ensures sufficient context is provided for meaningful skill gap analysis.
    """
    clean_jd = jd_text.strip() if jd_text else ""
    if len(clean_jd) < MIN_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The Job Description is too short. "
                "Please paste a complete job description with role responsibilities and requirements (at least 30 characters)."
            )
        )
    return clean_jd
