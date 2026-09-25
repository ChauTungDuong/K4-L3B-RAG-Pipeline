"""
Task 2 — Crawl bài viết/thông báo.

Hướng dẫn:
    1. Điền tối thiểu 5 URL công khai vào ARTICLE_URLS.
    2. Crawl từng URL bằng Crawl4AI.
    3. Lưu mỗi bài thành một JSON trong data/landing/news/.
    4. Giữ đủ url, title, date_crawled và content_markdown.

Cài browser trước khi chạy:
    python -m playwright install chromium
    
-> Dùng Firecrawl or bất cứ công cụ nào bạn quen    
"""

import asyncio
import json
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

ARTICLE_URLS = [
    "https://ts.hust.edu.vn/tin-tuc/quy-che-tuyen-sinh-dai-hoc-nam-2026",
    "https://ts.hust.edu.vn/tin-tuc/quy-dinh-ve-phuong-thuc-xet-tuyen-tai-nang-nam-2026",
    "https://ts.hust.edu.vn/tin-tuc/thong-tin-tuyen-sinh-dai-hoc-chinh-quy-nam-2026",
    "https://ts.hust.edu.vn/tin-tuc/du-kien-phuong-an-tuyen-sinh-dai-hoc-2026-cua-bach-khoa-ha-noi",
    "https://ts.hust.edu.vn/tin-tuc/bach-khoa-ha-noi-cong-bo-nguong-dau-vao-cac-nganh-vi-mach-ban-dan-nam-2026"
]

async def crawl_article(url: str) -> dict:
    import urllib.request
    import ssl
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    res = urllib.request.urlopen(req, context=ctx, timeout=10)
    page_html = res.read().decode('utf-8')
    
    soup = BeautifulSoup(page_html, "html.parser")
    title_tag = soup.find("h1", class_="title")
    title = title_tag.text.strip() if title_tag else "Unknown Title"
    
    date_tag = soup.find("p", class_="date-created")
    date_str = date_tag.text.strip() if date_tag else ""
    
    desc_tag = soup.find("div", class_="description")
    if desc_tag:
        content = md(str(desc_tag))
    else:
        content = md(page_html)
        
    import html
    content = html.unescape(content)
        
    return {
        "url": url,
        "title": html.unescape(title),
        "date_crawled": date_str,
        "content_markdown": content.strip()
    }


async def crawl_all() -> None:
    """Crawl và lưu từng bài thành một file JSON."""
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
