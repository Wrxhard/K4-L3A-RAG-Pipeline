"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.

Cài đặt:
    Dependency MarkItDown đã được khai báo trong pyproject.toml.
    
-> Hoặc dùng công cụ nào bạn quen khác Markitdown
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from markitdown import MarkItDown


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"
LEGAL_EXTENSIONS = {".pdf", ".doc", ".docx"}
REQUIRED_NEWS_FIELDS = {"url", "title", "date_crawled", "content_markdown"}
LOCAL_TESSDATA_DIR = Path(__file__).parent.parent / "data" / "ocr" / "tessdata"


def _write_non_empty_markdown(path: Path, content: str) -> None:
    """Ghi Markdown theo tên nguồn; ghi đè giúp chạy lại không tạo bản trùng."""
    normalized = content.strip()
    if not normalized:
        raise ValueError(f"Refusing to write an empty Markdown file: {path.name}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{normalized}\n", encoding="utf-8")


def _load_news_article(path: Path) -> dict[str, Any]:
    """Đọc và kiểm tra schema đầu vào để lỗi dữ liệu có thông báo rõ ràng."""
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path.name}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"News file must contain a JSON object: {path.name}")

    missing = REQUIRED_NEWS_FIELDS.difference(data)
    if missing:
        raise ValueError(f"{path.name} is missing fields: {', '.join(sorted(missing))}")

    empty = [field for field in REQUIRED_NEWS_FIELDS if not str(data[field]).strip()]
    if empty:
        raise ValueError(f"{path.name} has empty fields: {', '.join(sorted(empty))}")
    return data


def _find_tesseract() -> str:
    """Tìm Tesseract trong PATH hoặc vị trí cài phổ biến trên Windows."""
    executable = shutil.which("tesseract")
    if executable:
        return executable

    windows_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if windows_path.is_file():
        return str(windows_path)
    raise RuntimeError("Tesseract is required to OCR image-only PDF files")


def _ocr_pdf(path: Path) -> str:
    """Render từng trang PDF rồi OCR bằng model tiếng Việt cục bộ."""
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:
        raise RuntimeError("Install markitdown[pdf] to enable PDF OCR") from exc

    language_model = LOCAL_TESSDATA_DIR / "vie.traineddata"
    if not language_model.is_file():
        raise RuntimeError(f"Missing Vietnamese OCR model: {language_model}")

    tesseract = _find_tesseract()
    document = pdfium.PdfDocument(path)
    pages: list[str] = []
    # Scale 3 tương đương khoảng 216 DPI, đủ rõ mà không dùng quá nhiều bộ nhớ.
    with tempfile.TemporaryDirectory(prefix="rag-ocr-") as temporary_dir:
        temp_dir = Path(temporary_dir)
        for page_number, page in enumerate(document, start=1):
            image_path = temp_dir / f"page-{page_number}.png"
            page.render(scale=3).to_pil().save(image_path)
            process = subprocess.run(
                [
                    tesseract,
                    str(image_path),
                    "stdout",
                    "-l",
                    "vie",
                    "--tessdata-dir",
                    str(LOCAL_TESSDATA_DIR),
                ],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            page_text = process.stdout.strip()
            if page_text:
                pages.append(f"## Trang {page_number}\n\n{page_text}")
    return "\n\n".join(pages)


def convert_legal_docs() -> None:
    """Chuyển các tài liệu pháp lý được hỗ trợ sang Markdown."""
    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not legal_dir.is_dir():
        print(f"Skipped legal documents: directory not found: {legal_dir}")
        return

    converter = MarkItDown()
    source_paths = sorted(
        path
        for path in legal_dir.iterdir()
        if path.is_file()
        and not path.name.startswith(".")
        and path.suffix.lower() in LEGAL_EXTENSIONS
    )
    for path in source_paths:
        try:
            result = converter.convert(str(path))
            text_content = getattr(result, "text_content", "")
            # MarkItDown không OCR PDF scan, nên dùng Tesseract khi không có text layer.
            if not text_content.strip() and path.suffix.lower() == ".pdf":
                print(f"OCR fallback for image-only PDF: {path.name}")
                text_content = _ocr_pdf(path)
            _write_non_empty_markdown(output_dir / f"{path.stem}.md", text_content)
        except Exception as exc:
            # Một tài liệu hỏng/scan không được làm dừng việc xử lý cả thư mục.
            print(f"Skipped legal document: {path.name} ({exc})")
            continue
        print(f"Converted legal document: {path.name}")


def convert_news_articles() -> None:
    """Chuẩn hóa các bài viết JSON và giữ metadata ở đầu Markdown."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not news_dir.is_dir():
        print(f"Skipped news articles: directory not found: {news_dir}")
        return

    for path in sorted(news_dir.glob("*.json")):
        if path.name.startswith("."):
            continue
        data = _load_news_article(path)
        header = (
            f"# {str(data['title']).strip()}\n\n"
            f"**Source:** {str(data['url']).strip()}\n\n"
            f"**Crawled:** {str(data['date_crawled']).strip()}\n\n"
            "---\n\n"
        )
    # raise NotImplementedError("Implement convert_news_articles")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    convert_legal_docs()
    convert_news_articles()
    print(f"Saved Markdown to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
