# Báo cáo đóng góp cá nhân (Individual Contribution Report)

---

## 1. Thông tin cá nhân

- **Họ và tên:** Châu Tùng Dương
- **Mã học viên:** 2A202602822
- **Lớp / Nhóm:** K4-L3B
- **Vai trò:** Đội trưởng (Team Leader) — Phụ trách Kiến trúc Pipeline, Generation & UI
- **Repository:** https://github.com/ChauTungDuong/K4-L3B-RAG-Pipeline.git
- **Nhánh làm việc chính:** `ChauTungDuong` và `main`

---

## 2. Phần việc đã trực tiếp thực hiện

| Module / Deliverable | Việc tôi trực tiếp làm | File / Commit / PR | Trạng thái |
|---|---|---|---|
| **Quản trị Repo & Setup** | Thiết lập repository, phân chia kiến trúc zero-conflict, tối ưu hóa dependencies pyproject.toml | `TEAMMATES.md`<br>`HUONG_DAN_CHIA_VIEC.md`<br>`pyproject.toml` | Done |
| **Task 7 — Reranking RRF** | Cài đặt Reciprocal Rank Fusion theo rank, giữ nguyên input | `src/task7_reranking.py`<br>`tests/test_lab_visual_flow.py` | Code và unit test hoàn thành |
| **Task 8 — Vectorless Fallback** | Tích hợp PageIndex có cache PDF, timeout và ánh xạ trang được trích dẫn về SearchResult | `src/task8_pageindex_vectorless.py` | Code và unit test hoàn thành; cần key để thử dịch vụ thật |
| **Task 9 — Retrieval Pipeline** | Tích hợp dense, BM25, RRF một lần, fallback theo best dense score; thêm trace để minh họa từng bước | `src/task9_retrieval_pipeline.py` | Đã thử trên Chroma index 828 chunks; Dense, BM25 và Hybrid đều trả kết quả |
| **Task 10 — LLM Generation** | Reorder, context có ID nguồn, gọi provider theo `.env`, kiểm tra citation và safe refusal | `src/task10_generation.py` | Đã thử LLM thật với câu hỏi golden: trả lời 7,5 điểm môn Toán, dẫn đúng `news/article_05.md::chunk-1` |
| **Chatbot UI (Streamlit)** | Trang giải thích pipeline, hiển thị hai danh sách search, RRF, fallback, evidence và citation; hiển thị bộ câu hỏi tham chiếu | `app.py`<br>`src/trace_presentation.py`<br>`.streamlit/config.toml` | Streamlit AppTest render 3 tab, 19 tài liệu và 16 câu hỏi, không có exception; tắt file watcher gây nghẽn trang |
| **Evaluation A/B & Báo cáo** | Viết script đo A/B với cùng dữ liệu, prompt, top_k, evaluator; lưu case-level results và 4 metrics | `src/evaluate_ab.py`<br>`group_project/evaluation/results.json` (sinh khi chạy) | Golden dataset có 16 câu hỏi; phép đo thật bị Gemini HTTP 429 nên chưa có điểm A/B và chưa tạo `results.json` |

---

## 3. Quyết định kỹ thuật quan trọng

1. **Quyết định 1: Dùng điểm Cosine Distance của Dense Search làm căn cứ kích hoạt Fallback**
   - **Lý do / Evidence:** RRF score chỉ phản ánh thứ hạng tương đối (rank-based) giữa các danh sách chứ không đo lường độ tương đồng tuyệt đối của câu hỏi với tài liệu. Cosine similarity của Dense embedding là thước đo chuẩn xác nhất để nhận biết câu hỏi ngoài phạm vi (out-of-domain).
   - **Trade-off:** Cần hiệu chỉnh `SCORE_THRESHOLD` bằng câu hỏi trong và ngoài phạm vi sau khi corpus tuyển sinh được chốt; hiện chưa có cơ sở để khẳng định một con số cụ thể.

2. **Quyết định 2: Áp dụng chiến lược Reorder Context (Lost-in-the-middle)**
   - **Lý do / Evidence:** Các LLM thường chú ý tốt nhất ở phần đầu và phần cuối của context, trong khi các đoạn ở giữa dễ bị bỏ quên. Hàm `reorder_for_llm` đưa các chunk có điểm cao nhất ra 2 đầu.
   - **Trade-off:** Làm xáo trộn thứ tự score giảm dần gốc của retrieval, nhưng đổi lại tăng độ trung thực (faithfulness) và khả năng trích dẫn đúng của LLM.

---

## 4. Kiểm thử và kết quả

- **Các test đã kiểm tra:** `python -m unittest discover -s tests -p test_lab_visual_flow.py -v` — 11/11 đạt; chạy toàn bộ `pytest -q -p no:cacheprovider` trên `.venv` Python 3.13 — 30 đạt, 1 chưa đạt vì báo cáo đánh giá nhóm chưa có. Streamlit AppTest render 3 tab không có exception.
- **Dữ liệu và index:** Corpus Đại học Bách khoa Hà Nội 2026 có 19 file Markdown; Task 4 tạo 828 chunks trong Chroma. Truy vấn thực trả Dense, BM25 và Hybrid; câu hỏi đầu tiên trong golden dataset được trả lời có citation hợp lệ.
- **Đánh giá còn thiếu:** Golden dataset có 16 câu hỏi. Đánh giá A/B thật bị giới hạn HTTP 429 từ Gemini, chưa tạo được `group_project/evaluation/results.json` và `group_project/evaluation/RESULT.md`. Không có số liệu điểm nào được suy đoán hoặc điền thay.
- **Môi trường demo:** Dùng `.venv` Python 3.13; Streamlit đã khởi động và trả HTTP 200. Chưa kiểm tra PageIndex với dịch vụ cloud thật.
- **Xử lý đã được unit test:** RRF không mutate đầu vào; PageIndex lỗi không làm retrieval crash; câu trả lời thiếu citation trả safe refusal.

---

## 5. Điều còn hạn chế & Hướng phát triển

- **Hạn chế:** Khi số lượng chunk tăng lớn, việc gọi đồng thời dense search và BM25 rồi fuse có thể làm tăng nhẹ độ trễ (latency).
- **Hướng cải thiện nếu có thêm thời gian:** Tích hợp bộ lọc HyDE (Hypothetical Document Embeddings) hoặc reranker cross-encoder sâu hơn như BGE-Reranker.

---

## 6. Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc mình trực tiếp phụ trách và có thể giải thích, demo toàn bộ quy trình trước giảng viên.

- **Ngày:** 25/09/2026
- **Xác nhận:** Châu Tùng Dương
