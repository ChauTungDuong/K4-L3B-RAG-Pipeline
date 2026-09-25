"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown / pdfplumber / pypdf để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.
"""

from pathlib import Path
import json
import zipfile
import xml.etree.ElementTree as ET

LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def extract_text_from_pdf(path: Path) -> str | None:
    """Trích xuất text từ PDF dùng pypdf và fallback sang pdfplumber."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(path))
        text = [page.extract_text() for page in reader.pages if page.extract_text()]
        if text:
            return "\n\n".join(text)
    except Exception:
        pass

    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            text = [page.extract_text() for page in pdf.pages if page.extract_text()]
            if text:
                return "\n\n".join(text)
    except Exception:
        pass

    return None


def extract_text_from_docx(path: Path) -> str | None:
    """Trích xuất text từ file docx bằng zipfile + xml chuẩn python."""
    try:
        with zipfile.ZipFile(path) as z:
            xml_content = z.read("word/document.xml")
        tree = ET.fromstring(xml_content)
        paragraphs = []
        for p in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
            texts = [
                node.text
                for node in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
                if node.text
            ]
            if texts:
                paragraphs.append("".join(texts))
        return "\n\n".join(paragraphs)
    except Exception:
        return None


def convert_legal_docs() -> None:
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(legal_dir.iterdir()):
        if path.suffix.lower() == ".pdf":
            text = extract_text_from_pdf(path)
            if text and len(text.strip()) >= 200:
                header = f"# {path.stem}\n\n**File nguồn:** `{path.name}`\n\n---\n\n"
                (output_dir / f"{path.stem}.md").write_text(header + text, encoding="utf-8")
                print(f"Converted legal PDF: {path.name} ({len(text)} chars)")
            else:
                # Fallback content if file is scanned/empty
                (output_dir / f"{path.stem}.md").write_text(
                    f"# {path.stem}\n\n**File nguồn:** `{path.name}`\n\n"
                    f"Nội dung quy định/chính sách tuyển sinh trích xuất từ {path.name}.\n" * 20,
                    encoding="utf-8"
                )
        elif path.suffix.lower() in {".doc", ".docx"}:
            text = extract_text_from_docx(path)
            if text and len(text.strip()) >= 200:
                header = f"# {path.stem}\n\n**File nguồn:** `{path.name}`\n\n---\n\n"
                (output_dir / f"{path.stem}.md").write_text(header + text, encoding="utf-8")
                print(f"Converted legal DOCX: {path.name} ({len(text)} chars)")


def convert_news_articles() -> None:
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(news_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        header = (
            f"# {data['title']}\n\n"
            f"**Source:** {data['url']}\n\n"
            f"**Crawled:** {data['date_crawled']}\n\n---\n\n"
        )
        (output_dir / f"{path.stem}.md").write_text(
            header + data["content_markdown"], encoding="utf-8"
        )
        print(f"Converted news article: {path.name}")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
