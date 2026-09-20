"""Crawl public NEU admissions articles into JSON landing files."""

import asyncio
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://neu.edu.vn/thong-bao-ve-nguong-dam-bao-chat-luong-dau-vao-va-quy-doi-tuong-duong-diem-trung-tuyen-giua-cac-phuong-thuc-xet-tuyen-dai-hoc-chinh-quy-nam-2026/",
    "https://neu.edu.vn/thong-bao-ve-viec-huong-dan-thi-sinh-dang-ky-xet-tuyen-vao-dai-hoc-chinh-quy-nam-2026-cua-dh-ktqd-va-dang-ky-nguyen-vong-tren-he-thong-chung-cua-bo-gddt/",
    "https://neu.edu.vn/thong-bao-ve-ho-so-xet-tuyen-ket-hop-vao-dai-hoc-chinh-quy-nam-2026-cua-dh-ktqd-va-dang-ky-nguyen-vong-tren-he-thong-chung-cua-bo-gddt/",
    "https://neu.edu.vn/thong-bao-ve-viec-gia-han-thoi-gian-dang-ky-ho-so-xet-tuyen-ket-hop-va-xet-tuyen-theo-ket-qua-thi-tot-nghiep-thpt-vao-dai-hoc-chinh-quy-nam-2026/",
    "https://neu.edu.vn/thong-bao-ve-viec-ban-hanh-va-cong-bo-sach-gioi-thieu-cac-nganh-chuong-trinh-dao-tao-dai-hoc-chinh-quy-tuyen-sinh-nam-2026-cua-dai-hoc-kinh-te-quoc-dan/",
]


def _fallback_title(url: str) -> str:
    slug = unquote(urlparse(url).path.rstrip("/").rsplit("/", 1)[-1])
    return re.sub(r"[-_]+", " ", slug).strip() or url


def parse_article_html(html: str, url: str) -> dict:
    """Extract the crawler's stable article contract from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title_node = soup.find("meta", attrs={"property": "og:title"})
    title = title_node.get("content", "").strip() if title_node else ""
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True)
    if not title:
        heading = soup.find(["h1", "h2"])
        title = heading.get_text(" ", strip=True) if heading else _fallback_title(url)

    content_root = soup.find("article") or soup.find("main") or soup.body or soup
    for node in content_root.find_all(
        ["script", "style", "nav", "header", "footer", "aside", "form"]
    ):
        node.decompose()

    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in content_root.get_text("\n", strip=True).splitlines()
    ]
    content = "\n\n".join(line for line in lines if line)

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now(timezone.utc).isoformat(),
        "content_markdown": content,
    }


async def crawl_article(url: str) -> dict:
    """Fetch and parse one public article URL."""
    response = requests.get(
        url,
        headers={"User-Agent": "NEU-RAG-news-crawler/1.0"},
        timeout=30,
        verify=os.getenv("NEU_CRAWLER_VERIFY_TLS", "true").lower() != "false",
    )
    response.raise_for_status()
    return parse_article_html(response.text, url)


async def crawl_all() -> None:
    """Crawl and save each configured article as an individual JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for index, url in enumerate(ARTICLE_URLS, 1):
        try:
            article = await crawl_article(url)
            output = DATA_DIR / f"article_{index:02d}.json"
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Saved: {output}")
        except Exception as error:
            print(f"Failed: {url} — {error}")


if __name__ == "__main__":
    asyncio.run(crawl_all())
