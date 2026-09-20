import asyncio

from src.task2_crawl_news import crawl_article, parse_article_html


def test_parse_article_prefers_article_and_extracts_metadata():
    html = """
    <html>
      <head><title>Fallback page title</title></head>
      <body>
        <header>Site navigation</header>
        <article>
          <h1>NEU tuyển sinh đại học</h1>
          <p>Phương thức xét tuyển và chỉ tiêu năm 2025.</p>
          <p>Thông tin học phí được công bố theo chương trình.</p>
        </article>
        <footer>Footer links</footer>
      </body>
    </html>
    """

    result = parse_article_html(html, "https://neu.edu.vn/admissions")

    assert result["url"] == "https://neu.edu.vn/admissions"
    assert result["title"] == "Fallback page title"
    assert "NEU tuyển sinh đại học" in result["content_markdown"]
    assert "Site navigation" not in result["content_markdown"]
    assert result["date_crawled"]


def test_parse_article_falls_back_to_main_and_url_title():
    html = """
    <html>
      <body>
        <main><p>Điểm chuẩn và chỉ tiêu tuyển sinh NEU.</p></main>
      </body>
    </html>
    """

    result = parse_article_html(html, "https://neu.edu.vn/diem-chuan-neu-2025")

    assert result["title"] == "diem chuan neu 2025"
    assert result["content_markdown"] == "Điểm chuẩn và chỉ tiêu tuyển sinh NEU."


def test_crawl_article_fetches_url_and_raises_http_errors(monkeypatch):
    class FakeResponse:
        text = "<html><title>NEU</title><article><p>Admissions</p></article></html>"

        def raise_for_status(self):
            return None

    calls = {}

    def fake_get(url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("src.task2_crawl_news.requests.get", fake_get)

    result = asyncio.run(crawl_article("https://neu.edu.vn/admissions"))

    assert result["title"] == "NEU"
    assert result["content_markdown"] == "Admissions"
    assert calls["kwargs"]["timeout"] == 30
    assert "User-Agent" in calls["kwargs"]["headers"]
