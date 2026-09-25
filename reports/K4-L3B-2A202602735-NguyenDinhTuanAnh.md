# Báo cáo đóng góp cá nhân (Individual Contribution Report)

---

## 1. Thông tin cá nhân

- **Họ và tên:** Nguyễn Đình Tuấn Anh
- **Mã học viên:** 2A202602735
- **Lớp / Nhóm:** K4-L3B
- **Vai trò:** Thành viên — Phụ trách Kỹ thuật Dữ liệu, Indexing & Tìm kiếm (Data & Search Indexing)
- **Repository:** https://github.com/ChauTungDuong/K4-L3B-RAG-Pipeline.git
- **Nhánh làm việc chính:** `feature/data-and-search`

---

## 2. Phần việc đã trực tiếp thực hiện

| Module / Deliverable | Việc tôi trực tiếp làm | File / Commit / PR | Trạng thái |
|---|---|---|---|
| **Task 1 — Thu thập tài liệu** | Tìm kiếm và tải tối thiểu 3 tài liệu pháp lý/quy chế dạng PDF/DOCX (>1KB), lưu trữ đúng quy chuẩn | `src/task1_collect_legal_docs.py`<br>`data/landing/legal/` | In progress |
| **Task 2 — Crawl tin tức** | Crawl tối thiểu 5 bài viết thông báo công khai, trích xuất đầy đủ 4 trường metadata (url, title, date, markdown) | `src/task2_crawl_news.py`<br>`data/landing/news/` | In progress |
| **Task 3 — Chuẩn hóa Markdown** | Chuyển đổi toàn bộ PDF/DOCX và JSON sang Markdown chuẩn, đảm bảo dung lượng mỗi bài $\ge 200$ ký tự | `src/task3_convert_markdown.py`<br>`data/standardized/` | In progress |
| **Task 4 — Chunking & Indexing** | Chia nhỏ văn bản theo RecursiveCharacterTextSplitter (500/50), embed bằng Gemini API và upsert vào ChromaDB | `src/task4_chunking_indexing.py`<br>`chroma_db/` | In progress |
| **Task 5 — Semantic Search** | Tìm kiếm tương đồng ngữ nghĩa trên ChromaDB, chuyển cosine distance thành similarity score | `src/task5_semantic_search.py` | In progress |
| **Task 6 — Lexical Search (BM25)** | Xây dựng chỉ mục từ khóa BM25Okapi trên cùng tập corpus chunks, trả về SearchResult chuẩn contract | `src/task6_lexical_search.py` | In progress |
| **Golden Dataset (15 cases)** | Soạn thảo 15 cặp câu hỏi - câu trả lời - context trích dẫn bám sát nội dung dữ liệu thực tế đã crawl | `group_project/evaluation/golden_dataset.json` | In progress |

---

## 3. Quyết định kỹ thuật quan trọng

1. **Quyết định 1: Lựa chọn kích thước Chunking (Chunk Size = 500, Overlap = 50, Recursive)**
   - **Lý do / Evidence:** Kích thước 500 ký tự phù hợp với cấu trúc điều khoản trong các văn bản quy chế và bài báo thông báo ngắn. Overlap 50 ký tự giữ được tính liên kết giữa các câu tiếp giáp mà không làm tăng quá nhiều số lượng vector lưu trữ.
   - **Trade-off:** Chunk ngắn giúp định vị chính xác đoạn thông tin nhưng có thể làm phân tách các ý dài cần tổng hợp; điều này được bù đắp bằng kỹ thuật RRF gộp nhiều chunk liên quan.

2. **Quyết định 2: Sử dụng Gemini API (`text-embedding-004`) thay vì model cục bộ**
   - **Lý do / Evidence:** Việc chạy `sentence-transformers` trên máy cá nhân đòi hỏi cài đặt PyTorch (~2.5GB) gây nặng máy, tốn tài nguyên và tăng nguy cơ lỗi môi trường. Gemini API xử lý embedding nhanh, đồng bộ với mô hình sinh ở Task 10 và tiết kiệm thời gian cài đặt.
   - **Trade-off:** Phụ thuộc vào kết nối mạng và quota của Gemini API Key.

---

## 4. Kiểm thử và kết quả

- **Các test case / lệnh đã kiểm tra:**
  - `pytest tests/test_acceptance.py -k "corpus or standardized"` (xác nhận đủ số lượng và độ dài tài liệu).
  - `pytest tests/test_contracts.py -k "chunk or semantic or lexical"` (xác nhận đúng schema, không trùng ID, sắp xếp giảm dần).
- **Kết quả đạt được:**
  - 100% test contract của Task 4, 5, 6 đều passed.
  - Bộ dữ liệu standardized sẵn sàng cho toàn bộ pipeline hoạt động ổn định.
- **Lỗi đã phát hiện và cách xử lý:**
  - Ban đầu một số file crawl bị thiếu trường `date_crawled` hoặc rỗng nội dung $\to$ Đã bổ sung logic kiểm tra và fallback giá trị datetime hiện tại.

---

## 5. Điều còn hạn chế & Hướng phát triển

- **Hạn chế:** Các bảng biểu phức tạp trong file PDF gốc khi chuyển sang Markdown có thể bị mất cấu trúc định dạng chuẩn.
- **Hướng cải thiện nếu có thêm thời gian:** Ứng dụng OCR nâng cao hoặc các parser chuyên biệt như Unstructured/LlamaParse để trích xuất cấu trúc bảng biểu hoàn hảo hơn.

---

## 6. Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc mình trực tiếp phụ trách và có thể giải thích, chạy lại mã nguồn trước giảng viên.

- **Ngày:** 25/09/2026
- **Xác nhận:** Nguyễn Đình Tuấn Anh
