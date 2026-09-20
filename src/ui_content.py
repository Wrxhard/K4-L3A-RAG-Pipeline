"""Local content and presentation for the NEU demo (no model/API calls)."""

import base64
import json
from functools import lru_cache
from html import escape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


@lru_cache(maxsize=12)
def asset(name: str) -> str:
    path = ASSETS / name
    mime = {".png": "image/png", ".jpeg": "image/jpeg", ".webp": "image/webp"}[path.suffix]
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def safe_url(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


@lru_cache(maxsize=1)
def articles() -> list[dict]:
    items = []
    for path in sorted((ROOT / "data" / "landing" / "news").glob("*.json")):
        try:
            item = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(item, dict) and item.get("title") and safe_url(item.get("url")):
                items.append({**item, "filename": f"{path.stem}.md"})
        except (OSError, ValueError):
            continue
    return items


def source_details(source: dict) -> tuple[str, str | None]:
    """Recover original news titles/URLs when indexing retained only a filename."""
    metadata = source.get("metadata", {})
    filename = Path(metadata.get("source", "")).name
    article = next((item for item in articles() if item["filename"] == filename), {})
    title = article.get("title") or metadata.get("title") or filename or "Tài liệu"
    url = safe_url(metadata.get("url")) or safe_url(article.get("url"))
    return title.removesuffix(" – NEU"), url


def icon(name: str) -> str:
    paths = {
        "arrow": '<path d="M5 12h14m-6-6 6 6-6 6"/>',
        "down": '<path d="m6 9 6 6 6-6"/>',
        "book": '<path d="M4 4h6a3 3 0 0 1 3 3v14a4 4 0 0 0-4-3H4zm16 0h-4a3 3 0 0 0-3 3v14a4 4 0 0 1 4-3h3z"/>',
        "chat": '<path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a9.5 9.5 0 0 1 19 0Z"/><path d="M7 9h9M7 13h6"/>',
    }
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#07518d" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{paths[name]}</svg>'
    encoded = base64.b64encode(svg.encode()).decode("ascii")
    return f'<img class="ui-icon" src="data:image/svg+xml;base64,{encoded}" alt="" aria-hidden="true">'


def home_html() -> str:
    arrow = icon("arrow")
    nav = [
        ("Giới thiệu", "https://neu.edu.vn/gioi-thieu/"),
        ("Tin tức", "#thong-tin"),
        ("Sự kiện", "https://neu.edu.vn/events/"),
        ("Đào tạo", "https://daotaodaihoc.neu.edu.vn/"),
        ("Khoa học – Công nghệ", "https://khoahoc.neu.edu.vn/"),
        ("Hợp tác", "https://phonghtqt.neu.edu.vn/"),
        ("Tuyển sinh", "#tuyen-sinh"),
    ]
    links = "".join(
        f'<a href="{url}" ' + ('target="_blank" rel="noopener noreferrer" ' if url.startswith("https") else "")
        + f'>{label}{icon("down") if index < 6 else ""}</a>'
        for index, (label, url) in enumerate(nav)
    )
    news = articles()
    news_rows = "".join(
        f'<a class="news-row" href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">'
        f'<span class="news-number">0{index + 1}</span><span><small>THÔNG BÁO TUYỂN SINH</small>'
        f'<h3>{escape(item["title"].removesuffix(" – NEU"))}</h3></span>{arrow}</a>'
        for index, item in enumerate(news[:3])
    )
    legal_count = len(list((ROOT / "data" / "standardized" / "legal").glob("*.md")))
    hero = "neu-home.jpeg"
    return f"""
<div class="neu-home">
  <section class="neu-hero" aria-label="Đại học Kinh tế Quốc dân">
    <img class="hero-photo" src="{asset(hero)}" alt="Không gian Đại học Kinh tế Quốc dân" fetchpriority="high">
    <div class="hero-shade"></div>
    <header class="neu-header">
      <a class="brand" href="https://neu.edu.vn/" target="_blank" rel="noopener noreferrer" aria-label="Website chính thức Đại học Kinh tế Quốc dân">
        <img src="{asset('neu-logo.webp')}" alt="NEU 70 năm, 1956–2026">
      </a>
      <div class="header-right">
        <div class="utility-nav"><a href="https://neu.edu.vn/sinh-vien/" target="_blank" rel="noopener noreferrer">SINH VIÊN</a><a href="https://neu.edu.vn/" target="_blank" rel="noopener noreferrer">CÁN BỘ GIẢNG VIÊN</a><a href="https://alumni.neu.edu.vn/" target="_blank" rel="noopener noreferrer">CỰU SINH VIÊN</a><span class="demo-label">BẢN DEMO HỌC PHẦN</span></div>
        <nav class="desktop-nav" aria-label="Điều hướng chính">{links}</nav>
      </div>
      <details class="mobile-nav"><summary>Menu <span aria-hidden="true">☰</span></summary><nav aria-label="Điều hướng di động">{links}</nav></details>
    </header>
    <div class="hero-copy">
      <p class="eyebrow">ĐẠI HỌC KINH TẾ QUỐC DÂN</p>
      <h1>Tri thức hôm nay.<br><span>Vững bước tương lai.</span></h1>
      <p>Cùng bạn tìm hiểu chương trình đào tạo và<br class="desktop-break"> hành trình trở thành sinh viên NEU.</p>
      <a class="hero-cta" href="#tuyen-sinh">Khám phá tuyển sinh {arrow}</a>
    </div>
    <div class="hero-bottom"><span>NATIONAL ECONOMICS UNIVERSITY</span><a href="#tuyen-sinh">Khám phá NEU {icon('down')}</a><span>1956 — 2026</span></div>
  </section>
  <div class="notice-bar"><strong>THÔNG TIN TUYỂN SINH</strong><a href="#thong-tin">Tra cứu thông báo, phương thức xét tuyển và hướng dẫn dành cho thí sinh {arrow}</a></div>
  <section id="tuyen-sinh" class="admissions-section section-wrap">
    <div class="section-heading"><div><p class="eyebrow">BẮT ĐẦU HÀNH TRÌNH CỦA BẠN</p><h2>Tìm hiểu tuyển sinh NEU</h2></div><p>Thông tin từ tài liệu của trường.<br>Câu trả lời luôn đi cùng nguồn tham khảo.</p></div>
    <div class="topic-grid">
      <a class="topic-card" href="#thong-tin"><span class="topic-index">01 / TUYỂN SINH</span><h3>Phương thức<br>xét tuyển</h3><p>Điều kiện, đối tượng và các phương thức xét tuyển đại học chính quy.</p><span class="topic-link">Xem thông báo {arrow}</span></a>
      <a class="topic-card" href="https://courses.neu.edu.vn/" target="_blank" rel="noopener noreferrer"><span class="topic-index">02 / ĐÀO TẠO</span><h3>Ngành học &amp;<br>chương trình</h3><p>Tìm hiểu các chương trình đào tạo để lựa chọn hướng đi phù hợp.</p><span class="topic-link">Khám phá ngành học {arrow}</span></a>
      <a class="topic-card" href="#ho-tro"><span class="topic-index">03 / ĐỒNG HÀNH</span><h3>Hỏi đáp<br>cùng trợ lý NEU</h3><p>Đặt câu hỏi bằng ngôn ngữ tự nhiên và đối chiếu tài liệu tham khảo.</p><span class="topic-link">Tìm hiểu trợ lý {arrow}</span></a>
    </div>
  </section>
  <section id="thong-tin" class="news-section section-wrap">
    <div class="section-heading"><div><p class="eyebrow">THÔNG TIN DÀNH CHO THÍ SINH</p><h2>Thông báo tuyển sinh</h2></div><a class="text-link" href="https://neu.edu.vn/" target="_blank" rel="noopener noreferrer">Website chính thức {arrow}</a></div>
    <div class="news-layout"><div class="news-feature"><img src="{asset('neu-hero.webp')}" alt="Thư viện Đại học Kinh tế Quốc dân" loading="lazy"><div><span class="eyebrow">HỌC TẬP TẠI NEU</span><h3>Một hành trình mới,<br>nhiều cơ hội phía trước.</h3><p>Khám phá môi trường học tập và tìm lời giải đáp cho những câu hỏi của bạn.</p></div></div><div class="news-list">{news_rows or '<p>Chưa có thông báo trong bộ tài liệu.</p>'}</div></div>
  </section>
  <section id="ho-tro" class="assistant-section"><div class="section-wrap assistant-layout"><div class="assistant-symbol">{icon('chat')}</div><div><p class="eyebrow">TRỢ LÝ TUYỂN SINH NEU</p><h2>Bạn hỏi. Chúng tôi cùng tìm câu trả lời.</h2><p>Tra cứu {legal_count} tài liệu và {len(news)} bài viết trong bộ dữ liệu của nhóm.<br>Nhấn “Hỏi đáp tuyển sinh” ở góc phải để bắt đầu.</p></div><span class="assistant-note">Có trích dẫn nguồn<br>Hỗ trợ tiếng Việt</span></div></section>
  <footer class="neu-footer section-wrap"><div><strong>ĐẠI HỌC KINH TẾ QUỐC DÂN</strong><p>National Economics University</p></div><div><p>Demo học phần · RAG Pipeline</p><small>Giao diện tham khảo NEU. Đây không phải website chính thức của trường.</small></div></footer>
</div>"""
