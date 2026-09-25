# KẾ HOẠCH PHÂN CÔNG VÀ HƯỚNG DẪN THỰC HIỆN BÀI LAB 08 (3 TIẾNG)
**Dự án:** K4-L3B — Xây dựng và đánh giá RAG Pipeline  
**Repository:** https://github.com/ChauTungDuong/K4-L3B-RAG-Pipeline.git  
**Nhóm 2 thành viên:**
- **Châu Tùng Dương (2A202602822)** — Đội trưởng (Lead)
- **Nguyễn Đình Tuấn Anh (2A202602735)** — Thành viên

---

## 1. NGUYÊN TẮC LÀM VIỆC & PHÂN NHÁNH GIT (ZERO-CONFLICT)

Để hoàn thành trong vòng 3 tiếng, hai thành viên **hoạt động hoàn toàn song song trên 2 nhánh Git riêng biệt**, sửa các tệp tin độc lập (mutually exclusive) để khi merge vào `main` không bao giờ bị xung đột (conflict).

```
Nhánh: feature/data-and-search (Tuấn Anh)   |  Nhánh: feature/pipeline-and-ui (Dương)
─────────────────────────────────────────────┼────────────────────────────────────────
- src/task1_collect_legal_docs.py            |  - src/task7_reranking.py
- src/task2_crawl_news.py                    |  - src/task8_pageindex_vectorless.py
- src/task3_convert_markdown.py              |  - src/task9_retrieval_pipeline.py
- src/task4_chunking_indexing.py             |  - src/task10_generation.py
- src/task5_semantic_search.py               |  - app.py
- src/task6_lexical_search.py                |  - group_project/evaluation/RESULT.md
- data/landing/ và data/standardized/        |  - reports/RESULT.md
- group_project/evaluation/golden_dataset.json
```

---

## 2. BẢNG PHÂN CÔNG CHI TIẾT

| Thành viên | Nhánh Git | Nhiệm vụ (Tasks) | File chỉnh sửa chính | Lệnh Test độc lập |
| :--- | :--- | :--- | :--- | :--- |
| **Nguyễn Đình Tuấn Anh** | `feature/data-and-search` | **Task 1, 2, 3** (Data)<br>**Task 4, 5, 6** (Indexing & Search)<br>**Golden Dataset** | `data/`<br>`src/task1_collect_legal_docs.py`<br>`src/task2_crawl_news.py`<br>`src/task3_convert_markdown.py`<br>`src/task4_chunking_indexing.py`<br>`src/task5_semantic_search.py`<br>`src/task6_lexical_search.py`<br>`golden_dataset.json` | `pytest tests/test_acceptance.py -k "corpus or standardized"`<br>`pytest tests/test_contracts.py -k "chunk or semantic or lexical"` |
| **Châu Tùng Dương** | `feature/pipeline-and-ui` | **Task 7, 8, 9** (RRF & Fallback)<br>**Task 10** (LLM Citation)<br>**app.py** (Streamlit UI)<br>**Evaluation & Báo cáo** | `src/task7_reranking.py`<br>`src/task8_pageindex_vectorless.py`<br>`src/task9_retrieval_pipeline.py`<br>`src/task10_generation.py`<br>`app.py`<br>`group_project/evaluation/RESULT.md`<br>`reports/RESULT.md` | `pytest tests/test_contracts.py -k "rrf or retrieve or reorder or generation"`<br>`streamlit run app.py` |

---

## 3. LỘ TRÌNH THỰC HIỆN TRONG 3 TIẾNG (180 PHÚT)

### Giai đoạn 1 (00:00 - 00:15 | 15 phút): Khởi động & Tạo nhánh Git
1. **Chốt chủ đề:** *"Quy chế đào tạo & Dịch vụ sinh viên"* (học phí, học bổng, ký túc xá...). Nguồn công khai, PDF có sẵn, không bị chặn crawler.
2. **Khởi tạo nhánh Git:**
   - **Dương:**
     ```bash
     git checkout main
     git pull origin main
     git checkout -b feature/pipeline-and-ui
     ```
   - **Tuấn Anh:**
     ```bash
     git checkout main
     git pull origin main
     git checkout -b feature/data-and-search
     ```

---

### Giai đoạn 2 (00:15 - 01:15 | 60 phút): Code song song trên nhánh riêng

#### A. Phần việc của Tuấn Anh (`feature/data-and-search`):
- **Phút 15 - 45 (Task 1, 2, 3 - Dữ liệu):**
  - Đặt 3 file PDF chính sách (mỗi file > 1KB) vào `data/landing/legal/`.
  - Chạy `src/task2_crawl_news.py` crawl 5 bài viết lưu vào `data/landing/news/*.json` (có đủ `url`, `title`, `date_crawled`, `content_markdown`).
  - Viết `src/task3_convert_markdown.py` chuyển toàn bộ sang `data/standardized/legal/*.md` và `data/standardized/news/*.md` (mỗi file $\ge 200$ ký tự).
  - *Kiểm tra:* `pytest tests/test_acceptance.py -k "corpus or standardized"` $\to$ **PASS**.
- **Phút 45 - 75 (Task 4, 5, 6 - Indexing & Search):**
  - `src/task4_chunking_indexing.py`: `load_documents`, `chunk_documents` (RecursiveCharacterTextSplitter 500/50), `embed_texts` (BAAI/bge-m3 hoặc MiniLM), `get_collection` (ChromaDB cosine), `index_to_vectorstore`.
  - `src/task5_semantic_search.py`: Query ChromaDB, chuyển distance thành similarity `max(0.0, 1.0 - distance)`, trả về `retrieval_method="dense"`.
  - `src/task6_lexical_search.py`: Dùng `BM25Okapi` trên cùng corpus chunks, trả về `retrieval_method="bm25"`.
  - *Kiểm tra:* `pytest tests/test_contracts.py -k "chunk or semantic or lexical"` $\to$ **PASS**.
- **Đẩy code lên Git:**
  ```bash
  git add data/ src/task1_collect_legal_docs.py src/task2_crawl_news.py src/task3_convert_markdown.py src/task4_chunking_indexing.py src/task5_semantic_search.py src/task6_lexical_search.py
  git commit -m "feat: complete data pipeline, chunking, chromadb and bm25 search"
  git push -u origin feature/data-and-search
  ```

#### B. Phần việc của Dương (`feature/pipeline-and-ui`):
- **Phút 15 - 45 (Task 7, 8, 9 - Pipeline & Fallback):**
  - `src/task7_reranking.py`: Thuật toán RRF `sum(1 / (k + rank))` với $k=60$. Nhớ `item.copy()` trước khi thay đổi điểm và đặt `retrieval_method="hybrid"`.
  - `src/task8_pageindex_vectorless.py`: Viết fallback an toàn (nếu lỗi hoặc thiếu API key thì bắt lỗi gracefully, không làm crash).
  - `src/task9_retrieval_pipeline.py`: So sánh `best_dense_score < score_threshold`. Dưới threshold thì thử fallback PageIndex; nếu lỗi thì trả `hybrid`.
  - *Kiểm tra:* `pytest tests/test_contracts.py -k "rrf or retrieve"` $\to$ **PASS**.
- **Phút 45 - 75 (Task 10 & Streamlit App):**
  - `src/task10_generation.py`: `reorder_for_llm` (Lost-in-the-middle), `format_context`, `call_llm` (OpenAI / Gemini), `generate_with_citation` (trả safe refusal nếu thiếu bằng chứng).
  - `app.py`: Giao diện chat Streamlit, hiển thị câu trả lời, huy hiệu phương pháp truy xuất và `st.expander` xem chi tiết các nguồn trích dẫn.
  - *Kiểm tra:* `pytest tests/test_contracts.py -k "reorder or generation"` $\to$ **PASS**.
- **Đẩy code lên Git:**
  ```bash
  git add src/task7_reranking.py src/task8_pageindex_vectorless.py src/task9_retrieval_pipeline.py src/task10_generation.py app.py
  git commit -m "feat: complete rrf, fallback pipeline, llm citation and streamlit ui"
  git push -u origin feature/pipeline-and-ui
  ```

---

### Giai đoạn 3 (01:15 - 01:45 | 30 phút): Merge nhánh & Tích hợp End-to-End
1. **Dương (Lead) tiến hành merge cả 2 nhánh vào `main`:**
   ```bash
   git checkout main
   git pull origin main
   git merge feature/data-and-search
   git merge feature/pipeline-and-ui
   git push origin main
   ```
2. **Tuấn Anh cập nhật `main` mới nhất về máy:**
   ```bash
   git checkout main
   git pull origin main
   ```
3. **Chạy Index dữ liệu thật vào ChromaDB:**
   ```bash
   python -m src.task4_chunking_indexing
   ```
4. **Kiểm tra Contract Test toàn bộ hệ thống:**
   ```bash
   pytest tests/test_contracts.py -v
   ```
   *(Tất cả 11 tests phải Passed)*.
5. **Chạy thử Chatbot Streamlit:**
   ```bash
   streamlit run app.py
   ```
   - Thử câu hỏi trong domain: kiểm tra trích dẫn chính xác nguồn từ PDF/bài viết.
   - Thử câu hỏi ngoài domain: kiểm tra chatbot kích hoạt safe refusal an toàn.

---

### Giai đoạn 4 (01:45 - 02:30 | 45 phút): Đánh giá A/B & Viết Báo cáo RESULT.md
1. **Tuấn Anh:** Viết ít nhất **15 câu hỏi** vào `group_project/evaluation/golden_dataset.json` dựa trên các tài liệu đã crawl:
   - 5 câu hỏi từ khóa chính xác (mã văn bản, ngày tháng, tên phòng ban).
   - 5 câu hỏi ngữ nghĩa (điều kiện học bổng, mức học phí, chính sách ưu đãi).
   - 5 câu hỏi mở rộng, so sánh hoặc dễ nhầm lẫn giữa các quy định.
   - Mỗi câu đủ 3 trường: `question`, `expected_answer`, `expected_context`.
2. **Dương:** Chạy đo kiểm so sánh:
   - **Config A (Dense-only):** Chạy `retrieve(..., use_reranking=False)`.
   - **Config B (Hybrid + RRF):** Chạy `retrieve(..., use_reranking=True)`.
   - Thu thập 4 chỉ số: Faithfulness, Answer Relevance, Context Recall, Context Precision.
3. **Cả hai cùng hoàn thiện `RESULT.md`:**
   - **XÓA TOÀN BỘ CHỮ "TODO"** trong file (bắt buộc để pass test acceptance).
   - Điền bảng điểm tổng hợp Config A, Config B và Delta B - A.
   - Phân tích 3 câu hỏi thất bại kém nhất (Worst performers) với Root cause rõ ràng.
   - Đưa ra 3 đề xuất cải tiến (Recommendations).
   - **Lưu ý:** Copy file hoàn thiện vào cả 2 đường dẫn:
     - `group_project/evaluation/RESULT.md`
     - `reports/RESULT.md`

---

### Giai đoạn 5 (02:30 - 03:00 | 30 phút): Báo cáo cá nhân, Rà soát Test & Nộp bài
1. **Tạo 2 báo cáo cá nhân trong thư mục `reports/`:**
   - Dương: `reports/K4-L3B-2A202602822-ChauTungDuong.md`
   - Tuấn Anh: `reports/K4-L3B-2A202602735-NguyenDinhTuanAnh.md`
   - Copy từ `reports/INDIVIDUAL_REPORT.md` và điền chi tiết công việc của mình.
2. **Chạy kiểm thử tổng hợp trước khi nộp:**
   ```bash
   pytest tests/test_contracts.py -q
   pytest tests/test_acceptance.py -q
   pytest -q
   ```
   *Tất cả phải PASS 100%!*
3. **Commit & Push toàn bộ lên GitHub:**
   ```bash
   git add .
   git commit -m "docs: finalize evaluation report, individual reports and golden dataset"
   git push origin main
   ```
4. **Kiểm tra an toàn bảo mật:**
   - Đảm bảo `.env` không bị commit lên GitHub.
   - Nộp link repository `https://github.com/ChauTungDuong/K4-L3B-RAG-Pipeline.git` trên hệ thống VLearn.
