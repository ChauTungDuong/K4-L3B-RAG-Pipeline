# Kế hoạch triển khai RAG tuyển sinh đại học

## Mục tiêu và phạm vi

Hoàn thiện phần việc của Châu Tùng Dương: Task 7–10, ứng dụng Streamlit vừa demo vừa giải thích pipeline, và khung đánh giá A/B. Corpus chỉ gồm một trường và một kỳ tuyển sinh; tên trường, năm và nguồn cụ thể sẽ lấy từ dữ liệu do nhóm thu thập. Không dùng số liệu đánh giá giả.

## Hợp đồng giữa các phần

- Giữ nguyên public signatures trong `docs/MODULE_CONTRACTS.md`.
- `SearchResult` giữ `id`, `content`, `score`, `metadata`, `retrieval_method`.
- `GenerationResult` giữ `answer`, `sources`, `retrieval_source`.
- Trace chỉ là dữ liệu bổ sung cho UI; không thay đổi kết quả public API.
- Dense score, BM25 score và RRF score là ba thang đo khác nhau; chỉ cosine score gốc quyết định fallback.

## Công việc theo thứ tự

1. **RRF:** triển khai gộp theo ID, rank bắt đầu từ 1, thứ tự ổn định, không sửa input. Kiểm tra công thức, trùng ID và `top_k`.
2. **Fallback:** triển khai PageIndex có điều kiện khi có API key, timeout, ánh xạ kết quả về `SearchResult`; thiếu key trả `[]`. Không giả kết quả từ PageIndex.
3. **Retrieval và trace:** gọi dense và BM25 một lần mỗi truy vấn; fuse một lần; ghi ranked lists, best dense score, threshold, nhánh fallback và kết quả cuối vào trace. `retrieve()` dùng cùng lõi xử lý với UI.
4. **Generation:** reorder context không sửa input, đánh nhãn nguồn theo ID chunk, gọi provider được cấu hình, kiểm tra citation và safe refusal. UI nhận cùng trace với kết quả generation, không truy xuất lần hai.
5. **Streamlit:** trang gồm vấn đề, sơ đồ pipeline, chat, hai bảng kết quả Dense/BM25, bảng RRF, quyết định fallback, thẻ evidence, câu trả lời và nguồn; tab đánh giá đọc dữ liệu thật khi có.
6. **A/B:** chạy dense-only và hybrid + RRF trên cùng golden dataset, tắt fallback ở cả hai cấu hình trong phép đo này. Lưu case-level results và bảng tổng hợp; viết `RESULT.md` sau khi corpus và phép đo sẵn sàng.
7. **Tích hợp:** chạy contract/acceptance tests, thử một câu trong domain và một câu ngoài domain, kiểm tra nguồn dẫn và cập nhật báo cáo cá nhân theo kết quả thực.

## Phối hợp và điều kiện hoàn thành

Tuấn Anh bàn giao tối thiểu 3 tài liệu chính sách, 5 trang/bài tuyển sinh, Markdown chuẩn hóa, dense/BM25 chạy trên cùng chunk và 15 câu hỏi có `expected_answer`/`expected_context`. Bạn tích hợp sau mốc đó. Bài hoàn thành khi demo giải thích được từng bước từ query đến citation, test pass, số liệu A/B có thể chạy lại và không còn placeholder trong báo cáo.

## Kiểm chứng

- `pytest tests/test_contracts.py -q`
- `pytest tests/test_acceptance.py -q`
- `pytest -q`
- `streamlit run app.py` và thử hai loại câu hỏi

Nếu corpus, key hoặc provider chưa được bàn giao, ghi trạng thái thiếu dữ liệu rõ ràng trên UI; không ghi điểm hoặc kết luận A/B giả.

## Trạng thái thực hiện trong nhánh `ChauTungDuong`

- Đã triển khai Task 7–10, trace dùng chung cho UI, trang Streamlit và script `src/evaluate_ab.py`.
- Đã cập nhật PageIndex lên `0.2.19` để dùng `PageIndexClient` với cloud index và citation; phiên bản `0.2.8` ban đầu không khớp API này.
- Đã thêm kiểm tra độc lập bằng `unittest`; chạy lại sau mỗi thay đổi hành vi quan trọng.
- Chưa chạy demo và báo cáo A/B thật: nhánh hiện có 0 PDF, 0 JSON tin tức, 0 Markdown và golden dataset rỗng. Việc này phụ thuộc dữ liệu và search của nhánh Tuấn Anh.
- Môi trường mặc định là Python 3.14, không khớp `pyproject.toml` (`<3.14`); chưa có `pytest` hoặc `streamlit`. Cần dùng Python 3.10–3.13 và cài dự án trước khi kiểm tra end-to-end.
