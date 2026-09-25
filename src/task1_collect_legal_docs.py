"""
Task 1 — Thu thập tài liệu chính sách/quy định.

Hướng dẫn:
    1. Chọn chủ đề của nhóm.
    2. Tìm tối thiểu 3 tài liệu PDF/DOCX từ nguồn công khai.
    3. Lưu file gốc vào data/landing/legal/.
    4. Đặt tên không dấu và thể hiện đúng nội dung.

Ví dụ tài liệu: học phí, học bổng, ký túc xá, quy trình đăng ký.
Nếu website chặn crawler, hãy chọn nguồn công khai khác; không vượt WAF.
"""

from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory() -> None:
    """Tạo thư mục lưu tài liệu gốc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tải ít nhất 3 PDF từ nguồn công khai."""
    import urllib.request
    import ssl
    
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    sources = {
        "quy-che-tuyen-sinh.pdf": "https://hust.edu.vn/uploads/sys/tuyen-sinh/2026_05/4740_qd-dhbk-qcts.pdf",
        "thong-tin-tuyen-sinh-dai-hoc-2026.pdf": "https://hust.edu.vn/uploads/sys/tuyen-sinh/2023_06/thong-tin-tuyen-sinh-dai-hoc-2026f.pdf",
        "quy-dinh-xttn.pdf": "https://hust.edu.vn/uploads/sys/tuyen-sinh/2026_03/qui-dinh-ve-xttn-nam-2026-ky.pdf",
        "quy-dinh-dhbk-cap-nhat.pdf": "https://hust.edu.vn/uploads/sys/tuyen-sinh/2023_06/6888_qd-dhbk-cap-nhat.pdf",
        "nguong-diem-vi-mach-ban-dan.pdf": "https://hust.edu.vn/uploads/sys/news/2026_07/th_ng_b_o_v__ng__ng_ng_nh_vi_m_ch_b_n_d_n_n_m_2026_14.07.2026_final.pdf"
    }
    
    for filename, url in sources.items():
        print(f"Downloading {filename}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            res = urllib.request.urlopen(req, context=ctx, timeout=30)
            (DATA_DIR / filename).write_bytes(res.read())
            print(f"Saved {filename}")
        except Exception as e:
            print(f"Error downloading {filename}: {e}")


if __name__ == "__main__":
    setup_directory()
    download_documents()
