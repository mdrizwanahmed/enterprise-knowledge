from pathlib import Path
import fitz
from docx import Document

def extract_pages(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        result = []
        with fitz.open(path) as pdf:
            for number, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
                if text:
                    result.append({"page": number, "text": text})
        return result
    if suffix == ".docx":
        text = "\n".join(p.text for p in Document(path).paragraphs if p.text.strip())
        return [{"page": None, "text": text}] if text.strip() else []
    if suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        return [{"page": None, "text": text}] if text else []
    raise ValueError(f"Unsupported file type: {suffix}")
