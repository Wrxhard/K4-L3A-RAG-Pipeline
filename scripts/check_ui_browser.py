"""Browser smoke checks; run while Streamlit is serving on localhost:8510.

Install Playwright and Chromium if needed. This script does not call an LLM.
Screenshots go to the gitignored artifacts/neu-ui directory.
"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "neu-ui"


def check_layout(page):
    assert page.locator('[data-testid="stException"]').count() == 0
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "Horizontal overflow"
    for image in page.locator(".neu-home img, .chat-brand img").all():
        assert image.evaluate("i => i.complete && i.naturalWidth > 0"), "Missing image"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for width in (375, 768, 1024, 1440):
            page = browser.new_page(viewport={"width": width, "height": 960})
            page.goto("http://127.0.0.1:8510", wait_until="domcontentloaded")
            launcher = page.locator(".st-key-chat_launcher button")
            try:
                launcher.wait_for(timeout=25000)
            except Exception:
                page.screenshot(path=str(OUTPUT / "failure.png"), full_page=True)
                print(page.locator("body").inner_text()[:2000])
                raise
            page.locator(".hero-photo").wait_for()
            page.wait_for_timeout(500)
            check_layout(page)
            box = launcher.bounding_box()
            assert box and box["x"] >= 0 and box["x"] + box["width"] <= width
            if width <= 768:
                page.locator(".mobile-nav summary").click()
                assert page.locator(".mobile-nav nav").is_visible()
                page.locator(".mobile-nav summary").click()
            page.screenshot(path=str(OUTPUT / f"home-{width}.png"), full_page=True)
            page.locator("#tuyen-sinh").scroll_into_view_if_needed()
            page.wait_for_timeout(200)
            check_layout(page)
            assert page.locator(".topic-card").count() == 3
            assert page.locator(".news-row").count() >= 1
            page.screenshot(path=str(OUTPUT / f"home-content-{width}.png"))
            page.locator(".neu-footer").scroll_into_view_if_needed()
            assert page.locator(".neu-footer").is_visible()
            launcher.click()
            page.get_by_placeholder("Nhập câu hỏi tuyển sinh của bạn…").wait_for(timeout=15000)
            page.wait_for_timeout(300)
            check_layout(page)
            page.screenshot(path=str(OUTPUT / f"chat-{width}.png"), full_page=True)
            page.locator(".st-key-back_home button").click()
            launcher.wait_for()
            assert page.locator(".neu-hero").is_visible()
            results.append({"width": width, "navigation": "passed", "layout": "passed"})
            page.close()
        browser.close()
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
