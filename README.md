# Day 8 — RAG Pipeline

## Mục tiêu

Mỗi nhóm xây dựng một chatbot RAG trả lời câu hỏi từ bộ tài liệu do nhóm thu thập. Sản phẩm phải có hybrid retrieval, citation, giao diện chat và báo cáo đánh giá.

Nhóm tự chọn bài toán và thu thập dữ liệu phù hợp; repo không cung cấp dữ liệu mẫu.

## Sản phẩm phải nộp

- Repository nhóm chạy được.
- Tối thiểu 3 tài liệu chính sách và 5 bài viết/page do nhóm tự thu thập.
- Pipeline: convert → chunk → index → dense + BM25 → RRF → fallback → generation có citation.
- Chatbot Streamlit hiển thị câu trả lời và nguồn đã dùng.
- Golden dataset tối thiểu 15 câu; đánh giá 4 metric và so sánh A/B.
- `group_project/evaluation/RESULT.md`.
- Mỗi thành viên nộp báo cáo cá nhân theo template trong `group_project/ịndividual/INDIVIDUAL_REPORT.md`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
python -m playwright install chromium
cp .env.example .env
```

Điền API key cần dùng trong `.env`; không commit file này.

```bash
# 1. Thu thập và chuẩn hoá
python -m src.task1_collect_legal_docs
python -m src.task2_crawl_news
python -m src.task3_convert_markdown

# 2. Index và kiểm tra contract
python -m src.task4_chunking_indexing
pytest -q

# 3. Chạy sản phẩm
streamlit run app.py
```

## Lộ trình 3 giờ

| Mốc                  | Thời gian | Kết quả cần có                           |
| -------------------- | --------: | ---------------------------------------- |
| 0. Setup             |   10 phút | Môi trường và `.env` sẵn sàng            |
| 1. Data              |   25 phút | ≥3 legal, ≥5 news, Markdown đã chuẩn hoá |
| 2. Index & search    |   30 phút | ChromaDB, dense search và BM25 chạy được |
| 3. Fusion & fallback |   25 phút | RRF và fallback tuân thủ contract        |
| 4. Generation & UI   |   30 phút | Chatbot trả lời có citation              |
| 5. Evaluation        |   30 phút | 15+ Q&A, 4 metric, A/B comparison        |
| 6. Demo & handoff    |   30 phút | Test, report, demo và push repository    |

## Lưu ý quy tắc để có code quality tốt:

- Dense và BM25 nên cùng trả về `SearchResult` theo một schema.
- RRF chỉ nên dùng để gộp thứ hạng và chỉ chạy một lần.
- Fallback dùng cosine score gốc của dense retrieval.
- Threshold phải được hiệu chỉnh trên query in domain và out of domain, không có một con số đúng cho mọi corpus.

## Tài liệu

- [Module contracts](docs/MODULE_CONTRACTS.md): schema, interface và invariant mà code/test nên tuân theo.
- [Step-by-step guide](docs/STEP_BY_STEP.md): thứ tự triển khai và tiêu chí hoàn thành từng bước.
- [Grading rubric](docs/GRADING_RUBRIC.md): Rubric thang điểm.
- [Individual report](group_project/ịndividual/INDIVIDUAL_REPORT.md): template báo cáo cá nhân.
- [Suggested topics](docs/SUGGESTED_TOPICS.md): danh sách chủ đề tham khảo, không bắt buộc.

## Kiểm tra

```bash
# Contract tests
pytest tests/test_contracts.py -q

# Acceptance tests
pytest tests/test_acceptance.py -q

# Toàn bộ
pytest -q
```

## Demo tuyển sinh có giải thích từng bước

`app.py` là trang Streamlit cho một trường và một kỳ tuyển sinh. Tab **Bài toán & pipeline** giải thích luồng; tab **Demo từng bước** hiển thị Dense, BM25, RRF, quyết định fallback theo cosine score gốc, đoạn tài liệu đưa vào LLM và citation. Tab **Đánh giá A/B** chỉ hiện số liệu sau khi chạy đánh giá thật.

Sau khi nhóm thu thập dữ liệu, chạy Task 1–4 theo thứ tự ở trên và cấu hình `.env` với `LLM_PROVIDER`, `LLM_MODEL` cùng API key tương ứng. PageIndex là tùy chọn; muốn dùng cloud fallback thì điền `PAGEINDEX_API_KEY` và `PAGEINDEX_CHAT_MODEL` phù hợp với key LLM. PDF chính sách nằm trong `data/landing/legal/` sẽ được upload một lần, document ID được cache trong `.cache/`.

Dùng Python 3.10–3.13 theo `pyproject.toml`. Với PageIndex fallback, dự án dùng PageIndex Python SDK 0.2.19; nếu thiếu key hoặc dịch vụ không trả trang có citation, pipeline giữ kết quả hybrid và generation có thể từ chối xác minh.

```bash
python -m src.task4_chunking_indexing
streamlit run app.py
```

Đánh giá A/B dùng cùng golden dataset (ít nhất 15 câu hỏi), `top_k`, prompt, generator và evaluator. Script đặt `score_threshold=0` ở cả hai cấu hình để tắt fallback trong phép so sánh retrieval; PageIndex được demo riêng.

```bash
python -m src.evaluate_ab
```

Kết quả chi tiết được ghi vào `group_project/evaluation/results.json` và được UI đọc trực tiếp. Sau khi xem ba ca kém nhất và đối chiếu nguồn thật, điền số liệu cùng phân tích vào `group_project/evaluation/RESULT.md` và `reports/RESULT.md`. Khi chưa có corpus hoặc API key, UI báo trạng thái thiếu dữ liệu và không hiển thị kết quả giả.
