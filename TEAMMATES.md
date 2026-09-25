# Thông tin nhóm thực hiện dự án — Lab 08 RAG Pipeline

**Lớp:** K4-L3B  
**Repository:** https://github.com/ChauTungDuong/K4-L3B-RAG-Pipeline.git  

---

## Danh sách thành viên và phân công nhiệm vụ

| STT | Họ và tên | Mã học viên | Vai trò | Nhánh / Phần việc phụ trách |
|:---:|:---|:---:|:---:|:---|
| 1 | **Châu Tùng Dương** | **2A202602822** | **Đội trưởng (Leader)** | - Quản lý repo, điều phối kiến trúc & tích hợp pipeline<br>- Task 7: Reranking & RRF (`src/task7_reranking.py`)<br>- Task 8: PageIndex vectorless fallback (`src/task8_pageindex_vectorless.py`)<br>- Task 9: Retrieval pipeline (`src/task9_retrieval_pipeline.py`)<br>- Task 10: Generation có citation & safe refusal (`src/task10_generation.py`)<br>- Streamlit UI (`app.py`)<br>- Báo cáo đánh giá A/B (`RESULT.md`) & Báo cáo cá nhân |
| 2 | **Nguyễn Đình Tuấn Anh** | **2A202602735** | **Thành viên (Member)** | - Task 1: Thu thập tài liệu pháp lý / quy chế (`src/task1_collect_legal_docs.py`)<br>- Task 2: Crawl bài viết / tin tức (`src/task2_crawl_news.py`)<br>- Task 3: Chuẩn hóa Markdown (`src/task3_convert_markdown.py`)<br>- Task 4: Chunking, embedding & ChromaDB index (`src/task4_chunking_indexing.py`)<br>- Task 5: Semantic search (`src/task5_semantic_search.py`)<br>- Task 6: Lexical search BM25 (`src/task6_lexical_search.py`)<br>- Xây dựng bộ dữ liệu kiểm thử `golden_dataset.json` & Báo cáo cá nhân |

---

## Kế hoạch phối hợp và tích hợp

- **Nhánh chính (Main branch):** Tích hợp sản phẩm hoàn chỉnh, đảm bảo pass toàn bộ `tests/test_contracts.py` và `tests/test_acceptance.py`.
- **Đánh giá A/B:** Hai thành viên cùng xây dựng 15 câu hỏi chuẩn trong `group_project/evaluation/golden_dataset.json` và phân tích kết quả so sánh giữa Dense-only (Config A) và Hybrid + RRF (Config B).
