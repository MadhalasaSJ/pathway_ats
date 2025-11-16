import io
from typing import Union

import pdfplumber
import docx


def extract_text_from_pdf_bytes(b: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(b)) as pdf:
        for page in pdf.pages:
            p = page.extract_text()
            if p:
                text_parts.append(p)
    return "\n".join(text_parts)


def extract_text_from_docx_bytes(b: bytes) -> str:
    doc = docx.Document(io.BytesIO(b))
    paragraphs = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paragraphs)


def extract_text_from_file(uploaded_file) -> str:
    """
    Given a Streamlit UploadedFile-like object, read and extract text based on extension.
    Supports: PDF, DOCX, TXT
    """
    name = getattr(uploaded_file, "name", None)
    raw = uploaded_file.read()
    if not name:
        # Fallback: try to guess PDF
        try:
            return extract_text_from_pdf_bytes(raw)
        except Exception:
            return raw.decode("utf-8", errors="ignore")

    lower = name.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf_bytes(raw)
    elif lower.endswith(".docx"):
        return extract_text_from_docx_bytes(raw)
    elif lower.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore")
    else:
        # Attempt PDF first, then text
        try:
            return extract_text_from_pdf_bytes(raw)
        except Exception:
            return raw.decode("utf-8", errors="ignore")
