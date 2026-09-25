# Báo cáo đóng góp cá nhân (Individual Contribution Report)

---

## 1. Thông tin cá nhân

- **Họ và tên:** Châu Tùng Dương
- **Mã học viên:** 2A202602822
- **Lớp / Nhóm:** K4-L3B
- **Vai trò:** Đội trưởng (Team Leader) — Phụ trách Kiến trúc Pipeline, Generation & UI
- **Repository:** https://github.com/ChauTungDuong/K4-L3B-RAG-Pipeline.git
- **Nhánh làm việc chính:** `main` và `feature/pipeline-and-ui`

---

## 2. Phần việc đã trực tiếp thực hiện

| Module / Deliverable | Việc tôi trực tiếp làm | File / Commit / PR | Trạng thái |
|---|---|---|---|
| **Quản trị Repo & Setup** | Thiết lập repository, phân chia kiến trúc zero-conflict, tối ưu hóa dependencies pyproject.toml | `TEAMMATES.md`<br>`HUONG_DAN_CHIA_VIEC.md`<br>`pyproject.toml` | Done |
| **Task 7 — Reranking RRF** | Cài đặt thuật toán Reciprocal Rank Fusion `sum(1/(k+rank))`, chuẩn hóa format SearchResult không mutate đầu vào | `src/task7_reranking.py` | In progress |
| **Task 8 — Vectorless Fallback** | Xử lý fallback an toàn với PageIndex hoặc mock fallback khi API ngoài gặp sự cố | `src/task8_pageindex_vectorless.py` | In progress |
| **Task 9 — Retrieval Pipeline** | Tích hợp dense + sparse search, RRF 1 lần, kiểm tra ngưỡng fallback dựa trên best dense score | `src/task9_retrieval_pipeline.py` | In progress |
| **Task 10 — LLM Generation** | Kỹ thuật Reordering giảm lost-in-the-middle, format context kèm citation, gọi Gemini API, trả safe refusal | `src/task10_generation.py` | In progress |
| **Chatbot UI (Streamlit)** | Xây dựng giao diện hỏi đáp, hiển thị trích dẫn nguồn (title, file, score, retrieval_method), xử lý out-of-domain | `app.py` | In progress |
| **Evaluation A/B & Báo cáo** | Chạy benchmark so sánh Config A (Dense-only) vs Config B (Hybrid+RRF), đo 4 metrics, phân tích lỗi | `group_project/evaluation/RESULT.md`<br>`reports/RESULT.md` | In progress |

---

## 3. Quyết định kỹ thuật quan trọng

1. **Quyết định 1: Dùng điểm Cosine Distance của Dense Search làm căn cứ kích hoạt Fallback**
   - **Lý do / Evidence:** RRF score chỉ phản ánh thứ hạng tương đối (rank-based) giữa các danh sách chứ không đo lường độ tương đồng tuyệt đối của câu hỏi với tài liệu. Cosine similarity của Dense embedding là thước đo chuẩn xác nhất để nhận biết câu hỏi ngoài phạm vi (out-of-domain).
   - **Trade-off:** Cần hiệu chỉnh (calibrate) một ngưỡng `SCORE_THRESHOLD` phù hợp (khoảng 0.30 - 0.35) để tránh kích hoạt fallback nhầm cho các câu hỏi khó trong domain.

2. **Quyết định 2: Áp dụng chiến lược Reorder Context (Lost-in-the-middle)**
   - **Lý do / Evidence:** Các LLM thường chú ý tốt nhất ở phần đầu và phần cuối của context, trong khi các đoạn ở giữa dễ bị bỏ quên. Hàm `reorder_for_llm` đưa các chunk có điểm cao nhất ra 2 đầu.
   - **Trade-off:** Làm xáo trộn thứ tự score giảm dần gốc của retrieval, nhưng đổi lại tăng độ trung thực (faithfulness) và khả năng trích dẫn đúng của LLM.

---

## 4. Kiểm thử và kết quả

- **Các test case / lệnh đã kiểm tra:**
  - `pytest tests/test_contracts.py -k "rrf or retrieve or reorder or generation"`
  - `streamlit run app.py` (kiểm tra giao diện với câu hỏi trong chủ đề và câu hỏi ngoài phạm vi).
- **Kết quả trước / sau khi tối ưu:**
  - Trước: Pipeline dễ bị crash khi provider ngoài lỗi hoặc câu hỏi không có context.
  - Sau: Hệ thống trả về safe refusal đúng chuẩn `GenerationResult` với `sources=[]` và `retrieval_source="none"`.
- **Lỗi đã phát hiện và cách xử lý:**
  - Lỗi mutate dictionary gốc trong danh sách ranked list của Task 7 $\to$ Sửa bằng cách dùng `.copy()` từng phần tử trước khi gán điểm RRF mới.

---

## 5. Điều còn hạn chế & Hướng phát triển

- **Hạn chế:** Khi số lượng chunk tăng lớn, việc gọi đồng thời dense search và BM25 rồi fuse có thể làm tăng nhẹ độ trễ (latency).
- **Hướng cải thiện nếu có thêm thời gian:** Tích hợp bộ lọc HyDE (Hypothetical Document Embeddings) hoặc reranker cross-encoder sâu hơn như BGE-Reranker.

---

## 6. Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc mình trực tiếp phụ trách và có thể giải thích, demo toàn bộ quy trình trước giảng viên.

- **Ngày:** 25/09/2026
- **Xác nhận:** Châu Tùng Dương
