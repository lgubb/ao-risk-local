import io
import mimetypes
from pathlib import Path
from typing import Protocol
import pdfplumber
from docx import Document
from app.services.ocr_helper import ocr_pdf
import re


def clean_ocr_noise(text: str) -> str:
    """Nettoyage léger des artefacts OCR et césures.
    - Dé-césure: jointure mots coupés par tiret en fin de ligne.
    - Fusion de lettres espacées (ex: "D y s f o n c t i o n n e m e n t" -> "Dysfonctionnement").
    - Jointure de sauts de ligne au milieu d'un mot (a\nbc -> abc) pour lettres minuscules.
    - Compactage des espaces multiples.
    """
    if not text:
        return text

    # 1) Dé-césure en fin de ligne: "moti-\n f" -> "motif"
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # 2) Jointure de retours à la ligne au milieu d'un mot (minuscules)
    text = re.sub(r"([a-zà-ÿ])\s*\n\s*([a-zà-ÿ])", r"\1\2", text, flags=re.IGNORECASE)

    # 3) Fusion mots avec lettres séparées par espaces (>=4 lettres)
    def _fuse_spaced_letters(m: re.Match) -> str:
        return m.group(0).replace(" ", "")

    text = re.sub(r"((?:[A-Za-zÀ-ÿ]\s){3,}[A-Za-zÀ-ÿ])", _fuse_spaced_letters, text)

    # 4) Compactage des espaces multiples
    text = re.sub(r"[ \t]{2,}", " ", text)

    return text.strip()


class Parser(Protocol):
    def extract(self, file_bytes: bytes) -> str: ...


# ---------- Implémentations ----------
class TxtParser:
    def extract(self, file_bytes: bytes) -> str:
        return file_bytes.decode("utf-8", errors="ignore")


class PdfParser:
    def extract(self, file_bytes: bytes, with_pages: bool = False):
        texts = []
        pages = []
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    if page_text:
                        texts.append(page_text)
                    if with_pages:
                        pages.append({"page": i + 1, "text": page_text})

            # OCR fallback si aucun texte détecté
            if not texts or not "".join(texts).strip():
                print("[INFO] Aucun texte détecté, fallback OCR…")
                ocr_text = ocr_pdf(file_bytes)
                texts = [ocr_text]
                if with_pages:
                    pages = [{"page": i + 1, "text": t} for i, t in enumerate(ocr_text.split("\f"))]

        except Exception as e:
            print(f"[PDF ERROR] {e}")

        result = {"full_text": clean_ocr_noise("\n".join(texts).strip())}
        if with_pages:
            # Nettoyage page par page
            result["pages"] = [{"page": p["page"], "text": clean_ocr_noise(p.get("text", ""))} for p in pages]
        return result


class DocxParser:
    def extract(self, file_bytes: bytes) -> str:
        text = []
        try:
            doc = Document(io.BytesIO(file_bytes))
            text = [p.text for p in doc.paragraphs if p.text.strip()]
        except Exception as e:
            print(f"[DOCX ERROR] {e}")
        return "\n".join(text)


# Factory
def parser_factory(filename: str) -> Parser:
    ext = Path(filename).suffix.lower()

    if ext == ".txt":
        return TxtParser()
    if ext == ".pdf":
        return PdfParser()
    if ext in {".docx", ".doc"}:
        return DocxParser()

    # Fallback mimetype
    mime, _ = mimetypes.guess_type(filename)
    if mime == "application/pdf":
        return PdfParser()
    if mime in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }:
        return DocxParser()

    raise ValueError(f"Format non supporté : {filename}")


# Façade compat pour upload_routes
def extract_text_from_file(file) -> dict:
    """
    Extraction texte et pages depuis un UploadFile (FastAPI).
    Retourne { "full_text": str, "pages": [ { "page": int, "text": str } ] }
    """
    filename = file.filename.lower()
    file_bytes = file.file.read()
    file.file.seek(0)              

    if filename.endswith(".pdf"):
        parser = PdfParser()
        return parser.extract(file_bytes, with_pages=True)

    elif filename.endswith(".docx") or filename.endswith(".doc"):
        parser = DocxParser()
        text = parser.extract(file_bytes)
        clean = clean_ocr_noise(text)
        return {"full_text": clean, "pages": [{"page": 1, "text": clean}]}

    elif filename.endswith(".txt"):
        parser = TxtParser()
        text = parser.extract(file_bytes)
        clean = clean_ocr_noise(text)
        return {"full_text": clean, "pages": [{"page": 1, "text": clean}]}

    else:
        raise ValueError("Format non supporté. Utilisez PDF, DOCX ou TXT.")
