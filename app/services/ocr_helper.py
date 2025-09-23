import pytesseract
from pdf2image import convert_from_bytes
import os

# === Configuration Tesseract path & langues ===
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
os.environ["TESSDATA_PREFIX"] = "/opt/homebrew/share/tessdata"

def ocr_pdf(file_bytes: bytes) -> str:
    """Effectue OCR sur un PDF scanné."""
    text = []
    try:
        images = convert_from_bytes(file_bytes)
        for img in images:
            text.append(pytesseract.image_to_string(img, lang="fra"))
    except Exception as e:
        print(f"[OCR ERROR] {e}")
    return "\n".join(text)
