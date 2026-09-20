"""PageIndex-backed vectorless fallback retrieval."""

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fpdf import FPDF
from pageindex import PageIndexClient


load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CACHE_FILE = Path(__file__).parent.parent / "data" / "pageindex_cache.json"
POLL_INTERVAL_SECONDS = float(os.getenv("PAGEINDEX_POLL_INTERVAL_SECONDS", "1"))
POLL_TIMEOUT_SECONDS = float(os.getenv("PAGEINDEX_POLL_TIMEOUT_SECONDS", "30"))


def _read_cache() -> dict[str, str]:
    try:
        value = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_cache(cache: dict[str, str]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _source_key(path: Path) -> str:
    return path.relative_to(STANDARDIZED_DIR).as_posix()


def _markdown_to_pdf(path: Path, directory: Path) -> Path:
    """Create a temporary PDF because PageIndex's upload endpoint requires PDF."""
    pdf_path = directory / f"{path.stem}.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    font_candidates = (
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    font = next((candidate for candidate in font_candidates if candidate.exists()), None)
    if font:
        pdf.add_font("Unicode", fname=str(font))
        pdf.set_font("Unicode", size=10)
    else:
        pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(0, 5, path.read_text(encoding="utf-8"))
    pdf.output(str(pdf_path))
    return pdf_path


def _upload_path(path: Path, client: PageIndexClient) -> dict[str, Any] | None:
    if path.suffix.lower() == ".pdf":
        response = client.submit_document(str(path))
        return response if isinstance(response, dict) else None
    with tempfile.TemporaryDirectory(prefix="pageindex-") as temporary:
        pdf_path = _markdown_to_pdf(path, Path(temporary))
        response = client.submit_document(str(pdf_path))
        return response if isinstance(response, dict) else None


def upload_documents() -> None:
    """Upload uncached standardized Markdown documents to PageIndex."""
    if not PAGEINDEX_API_KEY or not STANDARDIZED_DIR.is_dir():
        return

    cache = _read_cache()
    try:
        client = PageIndexClient(PAGEINDEX_API_KEY)
    except Exception:
        return

    changed = False
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        source = _source_key(path)
        if source in cache:
            continue
        try:
            response = _upload_path(path, client)
            document_id = response.get("doc_id") if isinstance(response, dict) else None
            if isinstance(document_id, str) and document_id.strip():
                cache[source] = document_id
                changed = True
        except Exception:
            continue

    if changed:
        _write_cache(cache)


def _retrieval_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("results", "retrieval_results", "nodes", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    for key in ("data", "result", "retrieval"):
        value = payload.get(key)
        items = _retrieval_items(value)
        if items:
            return items
    return []


def _wait_for_retrieval(client: PageIndexClient, retrieval_id: str) -> list[dict[str, Any]]:
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    while time.monotonic() <= deadline:
        payload = client.get_retrieval(retrieval_id)
        items = _retrieval_items(payload)
        status = str(payload.get("status", "completed")).lower() if isinstance(payload, dict) else "completed"
        if items or status in {"completed", "complete", "success", "failed", "error"}:
            return items
        time.sleep(POLL_INTERVAL_SECONDS)
    return []


def _text_from_item(item: dict[str, Any]) -> str:
    for key in ("text", "content", "markdown", "node_text", "summary"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _result_from_item(
    item: dict[str, Any],
    *,
    doc_id: str,
    source: str,
    rank: int,
) -> dict[str, Any] | None:
    content = _text_from_item(item)
    if not content:
        return None

    raw_id = item.get("id") or item.get("node_id") or item.get("nodeId") or rank
    raw_score = item.get("score")
    score = float(raw_score) if isinstance(raw_score, (int, float)) else 1.0 / rank
    raw_page = item.get("page", item.get("page_number", item.get("page_num", 0)))
    try:
        chunk_index = max(0, int(raw_page))
    except (TypeError, ValueError):
        chunk_index = 0
    path = Path(source)
    doc_type = path.parts[0] if path.parts and path.parts[0] in {"legal", "news"} else "news"
    title = path.stem.replace("_", " ").replace("-", " ").strip()
    return {
        "id": f"{doc_id}::{raw_id}",
        "content": content,
        "score": score,
        "metadata": {
            "source": source,
            "title": title or source,
            "doc_type": doc_type,
            "url": None,
            "chunk_index": chunk_index,
        },
        "retrieval_method": "pageindex",
    }


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Return PageIndex nodes normalized as pageindex SearchResults."""
    if top_k <= 0 or not query.strip() or not PAGEINDEX_API_KEY:
        return []

    cache = _read_cache()
    if not cache:
        upload_documents()
        cache = _read_cache()
    if not cache:
        return []

    try:
        client = PageIndexClient(PAGEINDEX_API_KEY)
        results: list[dict] = []
        for source, doc_id in cache.items():
            response = client.submit_query(doc_id, query, thinking=False)
            retrieval_id = response.get("retrieval_id") if isinstance(response, dict) else None
            if not isinstance(retrieval_id, str) or not retrieval_id.strip():
                continue
            for rank, item in enumerate(_wait_for_retrieval(client, retrieval_id), 1):
                result = _result_from_item(item, doc_id=doc_id, source=source, rank=rank)
                if result is not None:
                    results.append(result)
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]
    except Exception:
        return []


if __name__ == "__main__":
    upload_documents()
