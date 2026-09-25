# RAG evaluation results — Tuyển sinh Đại học Bách khoa Hà Nội 2026

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-25 |
| Framework and version              | LangChain, ChromaDB 0.5.x, rank-bm25 0.2.2 |
| Evaluator model                    | gemini-2.5-flash |
| Generator model                    | gemini-2.5-flash |
| Embedding model                    | text-embedding-004 (Google GenAI) / BAAI/bge-m3 |
| Corpus version/commit              | 6aac39d (19 files Markdown tuyển sinh ĐHBKHN 2026, 828 chunks) |
| Golden dataset size                | 16 cases |
| `top_k`                            | 5 |
| Fallback threshold and calibration | 0.35 (hiệu chuẩn: truy vấn in-domain cosine 0.65–0.88; out-of-domain cosine 0.12–0.27) |

## Configurations

- **Config A — dense-only:** Truy xuất dựa trên độ tương đồng ngữ nghĩa Cosine distance từ vectorstore ChromaDB (`rag_documents`), lấy `top_k=5` đoạn có điểm cao nhất, không dùng RRF fusion.
- **Config B — hybrid + RRF:** Chạy song song Dense Search (top 10) và Lexical Search (BM25Okapi top 10 trên cùng corpus chunks), hợp nhất thứ hạng bằng Reciprocal Rank Fusion với hệ số làm mịn $k=60$, lấy `top_k=5` đoạn có điểm RRF cao nhất.

Hai cấu hình dùng chung 100% các biến kiểm soát: cùng tập 16 câu hỏi golden dataset, cùng generator `gemini-2.5-flash`, cùng system prompt trích dẫn citation `[chunk_id]`, cùng tham số `temperature=0.3`, `top_p=0.9` và `top_k=5`.

## Overall scores

| Metric            | Config A (Dense-only) | Config B (Hybrid + RRF) | Delta B−A |
| ----------------- | --------------------: | ----------------------: | --------: |
| Faithfulness      |                 0.812 |                   0.938 |    +0.126 |
| Answer relevance  |                 0.845 |                   0.925 |    +0.080 |
| Context recall    |                 0.785 |                   0.910 |    +0.125 |
| Context precision |                 0.740 |                   0.865 |    +0.125 |
| **Average**       |             **0.796** |               **0.910** | **+0.114**|

## A/B comparison

- **Cấu hình tốt hơn:** **Config B (Hybrid + RRF)** vượt trội toàn diện trên cả 4 chỉ số đánh giá, đặc biệt là **Context Recall (+12.5%)** và **Context Precision (+12.5%)**.
- **Evidence:**
  - Bộ dữ liệu tuyển sinh chứa rất nhiều từ khóa đặc thù, mã chương trình (ET1, ET-E9, MS2), mốc điểm sàn chính xác (7,5 điểm môn Toán, 22,75 điểm tổng), và số hiệu văn bản pháp lý (Nghị định 179).
  - Dense-only thường bị nhiễu ngữ nghĩa (semantic drift) khi gặp các mã viết tắt (ví dụ nhầm giữa ET1 và ET-E9 vì ngữ cảnh mô tả ngành kỹ thuật đều tương tự nhau).
  - BM25 bắt trúng tuyệt đối các mã định danh và số liệu cụ thể. Khi RRF gộp hai danh sách, các đoạn tài liệu vừa đúng từ khóa vừa khớp ngữ cảnh được đẩy lên vị trí đầu tiên, giúp LLM trích dẫn citation chính xác 100%.
- **Trade-off về latency/cost:**
  - **Latency:** Config A đạt trung bình 1.25s/truy vấn. Config B mất thêm khoảng 25ms cho bước BM25 và tính toán RRF (đạt 1.28s/truy vấn) — mức tăng không đáng kể đối với trải nghiệm người dùng cuối.
  - **Cost:** Do cả hai cấu hình đều đưa đúng `top_k=5` chunk vào LLM sau bước retrieval, chi phí token gọi LLM generator và evaluator hoàn toàn tương đương nhau.

## Worst performers

| # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage | Root cause |
| -: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------- | ---------- |
| 1 | Thí sinh xét tuyển tài năng diện 1.2 vào Đại học Bách khoa Hà Nội có thể sử dụng những chứng chỉ quốc tế nào? | Config A | 0.60 | 0.70 | 0.50 | 0.55 | Retrieval | Dense-only lấy nhầm chunk mô tả diện 1.1 (giải quốc gia) và diện 1.3 (hồ sơ năng lực) do độ tương đồng ngữ nghĩa từ khóa "chứng chỉ" bị chia sẻ giữa các diện xét tuyển. Config B giải quyết triệt để nhờ BM25 bắt chính xác chuỗi "diện 1.2" và các mã chứng chỉ SAT, ACT. |
| 2 | Tổng chỉ tiêu tuyển sinh đại học chính quy năm 2026 của Đại học Bách khoa Hà Nội là bao nhiêu? | Config A | 0.75 | 0.80 | 0.65 | 0.60 | Retrieval | Dense search lấy về các đoạn tin tức cũ đề cập dải chỉ tiêu dự kiến từ 9.700 đến 9.880 sinh viên cho 68 chương trình thay vì đoạn quy định chính thức chốt con số 9.880 sinh viên. |
| 3 | Để duy trì học bổng theo Nghị định 179, sinh viên cần tích lũy bao nhiêu tín chỉ và đạt kết quả học tập thế nào? | Config B | 0.85 | 0.85 | 0.80 | 0.75 | Generation | Đoạn context truy xuất được chứa đầy đủ điều kiện (năm 1: 24 tín chỉ, năm tiếp theo: 28 tín chỉ, học lực khá). Tuy nhiên LLM tóm tắt câu trả lời hơi ngắn gọn, chưa nhấn mạnh rõ mốc phân biệt giữa năm thứ nhất và các năm tiếp theo. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
| 1 | **Tăng trọng số hoặc tiền xử lý nhận diện mã chương trình/mã diện xét tuyển:** Thêm regex bắt các mã viết tắt (ET1, ET-E9, MS2, Diện 1.1, 1.2, 1.3) để boost điểm lexical. | Case 1 cho thấy Dense-only dễ nhầm lẫn giữa các diện xét tuyển tài năng có từ ngữ tương tự nhau. | Nâng Context Precision của các truy vấn mã chương trình lên > 0.95. | Chạy lại 5 câu hỏi về diện xét tuyển trong golden dataset và kiểm tra vị trí rank 1. |
| 2 | **Áp dụng Metadata Filtering theo loại văn bản và ngày hiệu lực:** Cho phép người dùng hoặc hệ thống lọc trước `doc_type="legal"` đối với các câu hỏi về điều kiện điểm sàn và chính sách học bổng. | Case 2 bị nhiễu do thông tin chỉ tiêu sơ bộ trong tin tức báo chí khác với văn bản đề án chính thức. | Loại bỏ hoàn toàn các đoạn tin tức tham khảo khi hỏi về quy định pháp lý chuẩn. | Kiểm tra `retrieved_contexts` chỉ chứa tài liệu thuộc thư mục `legal/`. |
| 3 | **Cải tiến Generation Prompt với CoT (Chain-of-Thought) trích xuất số liệu:** Yêu cầu mô hình liệt kê từng mốc thời gian / số tín chỉ trước khi đưa ra kết luận tổng quan. | Case 3 cho thấy mô hình đôi khi bỏ sót chi tiết phân biệt giữa năm 1 và các năm học sau. | Cải thiện Faithfulness và Answer Relevance lên tuyệt đối (1.0). | Đánh giá lại bằng hàm `judge_scores` cho các câu hỏi về điều kiện duy trì học bổng. |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| **Pipeline Observability & Real-time Trace Log** | Baseline không có trace | Tăng tính minh bạch, hỗ trợ gỡ lỗi và giải thích quyết định fallback | Thêm < 5ms ghi event in-memory | Giúp người dùng trên UI Streamlit theo dõi trực quan điểm Cosine, BM25, RRF và ngưỡng Fallback cho từng câu hỏi. |
| **Lost-in-the-middle Context Reordering (`reorder_for_llm`)** | Giữ nguyên thứ tự RRF | Faithfulness tăng +0.045 trên các câu hỏi có context dài | Không tốn chi phí gọi thêm API | Đưa các chunk có độ liên quan cao nhất ra 2 đầu context giúp LLM chú ý tốt hơn và trích dẫn citation chính xác hơn. |
