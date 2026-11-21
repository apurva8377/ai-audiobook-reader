import io
import re
import unicodedata
from pathlib import Path
import pymupdf
from PIL import Image
import pytesseract


def _needs_marathi_ocr(text: str) -> bool:
    if not text.strip():
        return True
    if "\ufffd" in text or any(unicodedata.category(ch) == "Co" for ch in text):
        return True
    # Broken/orphaned Devanagari vowel signs or virama
    if re.search(r"(?:^|\s)[\u0900-\u0903\u093A-\u094F\u0951-\u0957\u0962-\u0963]", text):
        return True
    if re.search(r"\u094D(?:\s|[\u093E-\u094D])", text):
        return True
    # Legacy KrutiDev/Shree-Lipi ASCII-encoded Marathi (high density of mid-word semicolons/symbols)
    if len(re.findall(r"[a-zA-Z][;~`^\\|][a-zA-Z]", text)) >= 3:
        return True
    return False


def _sanitize_text(raw_text: str) -> str:
    cleaned = []
    for ch in raw_text:
        cat = unicodedata.category(ch)
        if ch == "\ufffd" or cat in ("Co", "Cn", "Cs", "So") or (cat == "Cc" and ch not in ("\n", "\t")):
            continue
        cleaned.append(ch)
    text = "".join(cleaned)
    text = re.sub(r"(?:^|\s)[\u0900-\u0903\u093A-\u094F\u0951-\u0957\u0962-\u0963]+", " ", text)
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_clean_page(pdf_path: Path, page_num: int) -> str:
    cache_txt = Path("output/books") / pdf_path.stem / f"page_{page_num + 1}.txt"
    if cache_txt.exists():
        return cache_txt.read_text(encoding="utf-8")

    with pymupdf.open(pdf_path) as doc:
        if page_num < 0 or page_num >= len(doc):
            return ""
        page = doc[page_num]
        raw_text = page.get_text("text")

        if _needs_marathi_ocr(raw_text):
            pix = page.get_pixmap(dpi=180)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            ocr_text = pytesseract.image_to_string(img, lang="mar+eng")
            result = _sanitize_text(ocr_text)
        else:
            result = _sanitize_text(raw_text)

    cache_txt.parent.mkdir(parents=True, exist_ok=True)
    cache_txt.write_text(result, encoding="utf-8")
    return result
