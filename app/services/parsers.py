import io
import mimetypes
from pathlib import Path
from typing import Protocol

import pdfplumber
from docx import Document


class Parser(Protocol):
    def extract(self, file_bytes: bytes) -> str: ...


# ---------- implémentations ----------
class TxtParser:
    def extract(self, file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8", errors="ignore")


class PdfParser:
    def extract(self, file_bytes: bytes) -> str:
        text = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text() or "")
        return "\n".join(text)


class DocxParser:
    def extract(self, file_bytes: bytes) -> str:
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
# -------------------------------------


def parser_factory(filename: str) -> Parser:
    """
    Retourne le parser adapté à l'extension ou au mimetype.
    Soulève ValueError si format non supporté.
    """
    ext = Path(filename).suffix.lower()

    # 1) basique sur l'extension
    if ext == ".txt":
        return TxtParser()
    if ext == ".pdf":
        return PdfParser()
    if ext in {".docx", ".doc"}:
        return DocxParser()

    # 2) fallback mimetype
    mime, _ = mimetypes.guess_type(filename)
    if mime == "application/pdf":
        return PdfParser()
    if mime in {"application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"}:
        return DocxParser()

    raise ValueError(f"Format non supporté : {filename}")
