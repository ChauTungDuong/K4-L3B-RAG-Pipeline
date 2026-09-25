# Báo cáo đóng góp cá nhân (Individual Contribution Report)

---

## 1. Thông tin cá nhân

- **Họ và tên:** Nguyễn Đình Tuấn Anh
- **Mã học viên:** 2A202602735
- **Lớp / Nhóm:** K4-L3B
- **Vai trò:** Thành viên (Data & Retrieval Engineer) — Phụ trách Dữ liệu, Chuẩn hóa, Indexing & Search
- **Repository:** https://github.com/ChauTungDuong/K4-L3B-RAG-Pipeline.git
- **Nhánh làm việc chính:** `tuananh`, `feature/data-and-search` (đã đồng bộ vào `main`)

---

## 2. Phần việc đã trực tiếp thực hiện

| Module / Deliverable | Việc tôi trực tiếp làm | File / Commit / PR | Trạng thái |
|---|---|---|---|
| **Task 1 — Thu thập Legal Docs** | Tải và lưu trữ 13 văn bản chính sách/quy chế tuyển sinh gốc (.pdf, .docx > 1KB) của ĐHBK Hà Nội | `src/task1_collect_legal_docs.py`<br>`data/landing/legal/*` | Hoàn thành, 100% file hợp lệ |
| **Task 2 — Crawl News & Bài viết** | Crawl 5 bài viết tuyển sinh JSON đầy đủ metadata (`url`, `title`, `date_crawled`, `content_markdown`), giải mã sạch HTML entities, bảo toàn link đính kèm; xây dựng crawler riêng `crawl_hust.py` lọc 14 bài đúng khung thời gian 10/2025 – 08/2026 | `src/task2_crawl_news.py`<br>`crawl_hust.py`<br>`data/landing/news/*.json`<br>`data_craw/*` | Hoàn thành, sạch lỗi chính tả HTML entities |
| **Task 3 — Chuẩn hóa Markdown** | Xây dựng pipeline chuyển đổi đa tầng kết hợp `pypdf`, `pdfplumber` và `zipfile` XML cho file Word; trích xuất nguyên vẹn > 65.000 ký tự bảng điểm và phương án tuyển sinh; thêm Header Metadata | `src/task3_convert_markdown.py`<br>`data/standardized/legal/*.md`<br>`data/standardized/news/*.md` | Hoàn thành, tất cả file $\ge 200$ ký tự |
| **Task 4 — Chunking & ChromaDB Index** | Tải dữ liệu, chia 828 chunks bằng `RecursiveCharacterTextSplitter` (size 500, overlap 50), sinh vector embedding dùng model `all-MiniLM-L6-v2`, upsert idempotent vào ChromaDB với metric cosine | `src/task4_chunking_indexing.py`<br>`chroma_db/` | Hoàn thành, pass contract indexing |
| **Task 5 — Semantic Search (Dense)** | Vector hóa query qua `embed_texts()`, truy vấn ChromaDB, chuyển cosine distance thành similarity `max(0.0, 1.0 - distance)`, trả về `SearchResult` với `retrieval_method="dense"` | `src/task5_semantic_search.py` | Hoàn thành, pass unit test & contract |
| **Task 6 — Lexical Search (BM25)** | Triển khai BM25 trên cùng tập chunks với Task 4; tinh chỉnh sang thuật toán `BM25Plus` để triệt tiêu điểm âm/bằng 0 trên corpus nhỏ; trả về `SearchResult` với `retrieval_method="bm25"` | `src/task6_lexical_search.py` | Hoàn thành, pass contract search |
| **Golden Dataset & Đánh giá** | Xây dựng bộ dữ liệu kiểm thử gồm 16 câu hỏi Q&A grounded 100% từ tài liệu thực tế của ĐHBK Hà Nội có đủ `question`, `expected_answer`, `expected_context` | `group_project/evaluation/golden_dataset.json` | Hoàn thành, pass acceptance test |

---

## 3. Quyết định kỹ thuật quan trọng

1. **Quyết định 1: Xây dựng cơ chế trích xuất tài liệu Fallback đa tầng (`pypdf` $\to$ `pdfplumber` $\to$ `zipfile XML`)**
   - **Lý do / Evidence:** Khi chuyển đổi tài liệu tuyển sinh chính thức `thong-tin-tuyen-sinh-dai-hoc-2026.pdf`, thư viện `pypdf` gặp lỗi cấu trúc PDF nội bộ (`unsupported operand type(s) for +: 'float' and 'IndirectObject'`) và file Word `.docx` bị lỗi giải mã nhị phân. Việc bổ sung `pdfplumber` và bộ parser XML thuần cho `.docx` đã cứu được toàn bộ hơn 65.000 ký tự văn bản chứa bảng điểm và chỉ tiêu chi tiết mà không cần thêm phụ thuộc ngoài cồng kềnh.
   - **Trade-off:** Thời gian xử lý khi convert lần đầu tăng thêm khoảng 2–3 giây, nhưng dữ liệu chuẩn hóa sang Markdown có chất lượng cao nhất, cung cấp đầy đủ bằng chứng thực tế cho RAG.

2. **Quyết định 2: Sử dụng thuật toán `BM25Plus` thay cho `BM25Okapi` truyền thống**
   - **Lý do / Evidence:** Công thức IDF của `BM25Okapi` sẽ gán trọng số âm hoặc bằng 0 cho các từ khóa xuất hiện trong $> 50\%$ số chunk của corpus. Đối với tập tài liệu tuyển sinh ĐHBK (nơi các từ khóa như "tuyển sinh", "Bách khoa", "điểm", "xét tuyển" xuất hiện rất dày đặc), `BM25Okapi` thường trả về điểm $\le 0$ và làm rớt các chunk liên quan. Việc chuyển sang `BM25Plus` với cận dưới chặn dương ($+ \delta$) giúp mọi chunk chứa từ khóa đều có score dương hợp lệ.
   - **Trade-off:** Cần cài đặt thư viện `rank_bm25` hỗ trợ biến thể Plus, nhưng đổi lại danh sách xếp hạng từ khóa ổn định và tương thích hoàn hảo với bước gộp RRF ở Task 7.

---

## 4. Kiểm thử và kết quả

- **Acceptance Tests (Data & Golden Dataset):**
  ```bash
  pytest tests/test_acceptance.py -k "corpus or standardized or golden" -q
  # Kết quả: 4 passed in 0.01s (100% ĐẠT)
  ```
  - `test_corpus_has_required_legal_documents`: 13 file PDF/DOCX $> 1\text{ KB}$ (vượt yêu cầu $\ge 3$).
  - `test_corpus_has_required_news_with_metadata`: 5 file JSON đầy đủ 4 trường metadata (đạt $\ge 5$).
  - `test_standardized_output_covers_both_source_types`: Toàn bộ các file Markdown đều $\ge 200$ ký tự.
  - `test_golden_dataset_has_15_grounded_cases`: 16/15 cases Q&A grounded chuẩn xác.

- **Contract Tests (Chunking, Semantic & Lexical):**
  ```bash
  pytest tests/test_contracts.py -k "chunk or semantic or lexical" -q
  # Kết quả: 3 passed in 4.08s (100% ĐẠT)
  ```
  - `test_chunking_contract_and_no_duplication`: ID duy nhất, không nhân bản khi index lại.
  - `test_semantic_search_returns_dense_contract`: Đúng schema `SearchResult`, `retrieval_method="dense"`, score giảm dần trong $[0, 1]$.
  - `test_lexical_search_returns_bm25_contract`: Đúng schema `SearchResult`, `retrieval_method="bm25"`, score giảm dần $> 0$.

- **Kiểm tra chạy module độc lập:** Toàn bộ các lệnh sau đều chạy thành công trên terminal:
  - `python -m src.task1_collect_legal_docs`
  - `python -m src.task2_crawl_news`
  - `python -m src.task3_convert_markdown`
  - `python -m src.task4_chunking_indexing` (Index thành công 828 chunks vào ChromaDB)
  - `python -m src.task5_semantic_search`
  - `python -m src.task6_lexical_search`

---

## 5. Điều còn hạn chế & Hướng phát triển

- **Hạn chế:**
  - Một số bảng biểu phức tạp trong file PDF (ví dụ bảng quy đổi tổ hợp điểm) khi trích xuất text đơn thuần có thể bị mất cấu trúc hàng/cột hoàn chỉnh, làm giảm nhẹ độ chính xác khi câu hỏi đòi hỏi tra cứu theo tọa độ ô.
  - Thời gian tải model embedding `all-MiniLM-L6-v2` lần đầu phụ thuộc vào kết nối mạng HuggingFace.
- **Hướng phát triển:**
  - Nghiên cứu ứng dụng các công cụ OCR/Layout-aware parser (như Nougat hoặc Docling) để chuyển đổi bảng biểu PDF thành cấu trúc bảng Markdown / HTML chuẩn.
  - Áp dụng kỹ thuật Semantic Chunking (cắt đoạn theo tiêu đề Điều/Khoản của văn bản quy chế) thay vì cắt đoạn theo số lượng ký tự cố định để giữ trọn vẹn ngữ nghĩa của từng điều luật.

---

## 6. Xác nhận đóng góp

Tôi xác nhận toàn bộ nội dung trong báo cáo này phản ánh trung thực phần việc tôi trực tiếp thiết kế, lập trình và kiểm thử trong dự án nhóm Lab 08 RAG Pipeline.

- **Ngày:** 25/09/2026
- **Xác nhận:** Nguyễn Đình Tuấn Anh
