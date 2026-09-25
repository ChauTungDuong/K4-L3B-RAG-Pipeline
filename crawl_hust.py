import urllib.request
import urllib.parse
import ssl
import re
import os
import html
import datetime

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Base URLs and output directory
sources = [
    "https://ts.hust.edu.vn/p/dai-hoc",
    "https://ts.hust.edu.vn/b/tin-tuc-dai-hoc"
]
output_dir = "data_craw"
legal_dir = os.path.join("data", "landing", "legal")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(legal_dir, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def clean_html_entities(text: str) -> str:
    """Repeatedly unescape HTML entities and normalize whitespace."""
    if not text:
        return ""
    text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
    while '&' in text and re.search(r'&[a-zA-Z0-9#]+;', text):
        new_text = html.unescape(text)
        if new_text == text:
            break
        text = new_text
    return text

def normalize_download_url(url: str) -> str:
    """Fix common host and scheme issues for hust.edu.vn attachments."""
    url = url.strip()
    if url.startswith("http://"):
        url = "https://" + url[7:]
    if "www.hust.edu.vn" in url:
        url = url.replace("www.hust.edu.vn", "hust.edu.vn")
    return url

def download_file(file_url: str, target_dirs: list[str]) -> str:
    """Download a file (PDF/DOCX) if not already present."""
    norm_url = normalize_download_url(file_url)
    parsed = urllib.parse.urlparse(norm_url)
    fname = os.path.basename(parsed.path)
    if not fname:
        return ""
    
    print(f"  [ATTACHMENT] Downloading {fname} from {norm_url}...")
    try:
        req = urllib.request.Request(norm_url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()
        
        for d in target_dirs:
            out_path = os.path.join(d, fname)
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"    -> Saved {out_path} ({len(data)} bytes)")
        return fname
    except Exception as e:
        print(f"    -> Error downloading {norm_url}: {e}")
        return ""

def extract_article_content(page_html: str, base_url: str):
    """Extract clean title, date, body with preserved links, and download attachments."""
    soup = BeautifulSoup(page_html, 'html.parser')
    
    # 1. Extract title
    title_tag = soup.find('h1', class_='title') or soup.find('title')
    title = clean_html_entities(title_tag.get_text(strip=True) if title_tag else "No Title")
    
    # 2. Extract date
    date_tag = soup.find('p', class_='date-created')
    date_str = date_tag.get_text(strip=True) if date_tag else ""
    doc_date = None
    m = re.search(r'(\d{1,2})-(\d{1,2})-(\d{4})', date_str)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        doc_date = datetime.date(year, month, day)
    
    # 3. Extract description / body
    desc = soup.find('div', class_='description') or soup.find('div', class_='content') or soup.body
    
    # Process links inside description
    if desc:
        # Preserve links in <a> tags
        for a in desc.find_all('a', href=True):
            raw_href = a['href'].strip()
            full_href = urllib.parse.urljoin(base_url, raw_href)
            link_text = clean_html_entities(a.get_text(strip=True))
            
            # Check if link points to a PDF or DOCX file
            lower_href = full_href.lower()
            if lower_href.endswith('.pdf') or lower_href.endswith('.docx') or '/uploads/sys/' in lower_href:
                download_file(full_href, [output_dir, legal_dir])
            
            if link_text:
                a.replace_with(f" {link_text} ({full_href}) ")
            else:
                a.replace_with(f" ({full_href}) ")
        
        # Add newlines for block elements
        for br in desc.find_all('br'):
            br.replace_with('\n')
        for block in desc.find_all(['p', 'div', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'tr']):
            block.insert_before('\n')
            block.insert_after('\n')
            
        raw_text = desc.get_text()
    else:
        raw_text = soup.get_text()

    # Format into clean paragraphs
    lines = []
    for line in raw_text.splitlines():
        cleaned_line = clean_html_entities(line)
        cleaned_line = re.sub(r'[ \t]+', ' ', cleaned_line).strip()
        # Remove web action buttons noise
        if cleaned_line in ['Lưu tin', 'Bình luận', 'Chia sẻ', 'Chia sẻ bài viết']:
            continue
        if cleaned_line:
            lines.append(cleaned_line)
            
    content_text = '\n\n'.join(lines)
    content_text = clean_html_entities(content_text)
    
    return title, date_str, doc_date, content_text

def collect_links() -> list[str]:
    """Find all article links from target sources."""
    links = []
    seen = set()
    for src in sources:
        print(f"Scanning {src}...")
        try:
            req = urllib.request.Request(src, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                page_html = resp.read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(page_html, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/tin-tuc/' in href:
                    full_link = urllib.parse.urljoin('https://ts.hust.edu.vn', href)
                    if full_link not in seen:
                        seen.add(full_link)
                        links.append(full_link)
        except Exception as e:
            print(f"Error scanning {src}: {e}")
    return links

def main():
    print("=== STARTING HUST CRAWLER ===")
    links = collect_links()
    print(f"Total discovered article links: {len(links)}")
    
    # Filter dates: From October 1, 2025 to August 9, 2026
    min_date = datetime.date(2025, 10, 1)
    max_date = datetime.date(2026, 8, 9)
    print(f"Filtering articles published between {min_date} and {max_date}...\n")
    
    crawled_count = 0
    for link in links:
        slug = link.rstrip('/').split('/')[-1]
        try:
            req = urllib.request.Request(link, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                page_html = resp.read().decode('utf-8', errors='ignore')
            
            title, date_str, doc_date, content_text = extract_article_content(page_html, link)
            
            # Check date criteria
            if doc_date and not (min_date <= doc_date <= max_date):
                print(f"[SKIP] Date {doc_date} out of range: {title}")
                continue
            elif not doc_date:
                print(f"[SKIP] No valid date found: {title}")
                continue
                
            print(f"[CRAWL] Date: {doc_date} | Title: {title}")
            
            # Write to data_craw/{slug}.txt
            out_file = os.path.join(output_dir, f"{slug}.txt")
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(f"{link}\n")
                f.write(f"{title}\n\n")
                f.write(f"Ngày đăng: {date_str}\n\n")
                f.write(f"{content_text}\n")
            
            crawled_count += 1
            print(f"  -> Saved {out_file}")
            
        except Exception as e:
            print(f"Error crawling {link}: {e}")
            
    print(f"\n=== CRAWL COMPLETE: Successfully processed {crawled_count} articles ===")

if __name__ == "__main__":
    main()
