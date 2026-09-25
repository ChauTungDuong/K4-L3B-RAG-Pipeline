"""Demo and visual explainer for the admissions RAG lab."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.task10_generation import generate_with_trace
from src.pipeline_observability import new_request_id, recent_events, record_event, safe_error
from src.trace_presentation import fusion_rows, search_rows


ROOT = Path(__file__).parent
EVALUATION_PATH = ROOT / "group_project" / "evaluation" / "results.json"
GOLDEN_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
STANDARDIZED_DIR = ROOT / "data" / "standardized"

st.set_page_config(page_title="RAG tuyển sinh | Lab 08", page_icon="🎓", layout="wide")
st.markdown(
    """<style>
    .block-container {max-width: 1320px; padding-top: 2rem;}
    .hero {background: linear-gradient(110deg,#113a52,#236382); color:white;
           padding:2rem 2.2rem; border-radius:20px; margin-bottom:1.4rem;}
    .hero h1 {color:white; margin:0; font-size:2.35rem;}
    .hero p {color:#e0f2f8; font-size:1.08rem; margin:.65rem 0 0;}
    .step {background:#eef7fa; color:#163447; border-left:4px solid #1a8ba8; border-radius:9px;
           padding:.75rem 1rem; min-height:6rem; margin-bottom:.5rem;}
    .step strong {color:#11506b;}
    </style>""",
    unsafe_allow_html=True,
)


def render_sources(sources: list[dict], title: str) -> None:
    st.subheader(title)
    if not sources:
        st.info("Không có đoạn tài liệu đủ điều kiện làm bằng chứng.")
        return
    for index, row in enumerate(sources, 1):
        meta = row["metadata"]
        with st.expander(f"{index}. {meta['title']} · {row['id']}", expanded=index == 1):
            st.caption(
                f"Nguồn: {meta['source']} | Phương pháp: {row['retrieval_method']} | "
                f"Điểm trong phương pháp này: {float(row['score']):.4f}"
            )
            st.write(row["content"])
            if meta.get("url"):
                st.link_button("Mở tài liệu gốc", meta["url"])
            else:
                local_pdf = ROOT / "data" / "landing" / "legal" / Path(meta["source"]).name
                if local_pdf.is_file():
                    st.download_button(
                        "Tải tài liệu PDF gốc", local_pdf.read_bytes(),
                        file_name=local_pdf.name, mime="application/pdf",
                        key=f"download-{title}-{index}-{row['id']}",
                    )
            if meta.get("page"):
                st.caption(f"Trang PDF: {meta['page']}")


def render_events(events: list[dict]) -> None:
    if not events:
        st.info("Chưa có bước xử lý nào được ghi lại.")
        return
    st.dataframe(
        [{"Thời gian": event.get("time", ""), "Bước": event.get("stage", ""),
          "Trạng thái": event.get("status", ""), "Chi tiết": event.get("message", ""),
          "Lỗi": event.get("error", ""),
          "Số đoạn": str(event["count"]) if "count" in event else "",
          "ms": str(event["elapsed_ms"]) if "elapsed_ms" in event else ""}
         for event in events],
        hide_index=True, use_container_width=True,
    )


def render_trace(trace: dict, sources: list[dict]) -> None:
    st.markdown("### 1. Tìm ứng viên bằng hai cách")
    dense_col, bm25_col = st.columns(2)
    with dense_col:
        st.markdown("**Dense · gần nhau về ngữ nghĩa**")
        st.caption("Điểm cosine similarity: cao hơn nghĩa là gần câu hỏi hơn.")
        if trace.get("dense"):
            st.dataframe(search_rows(trace["dense"]), hide_index=True, use_container_width=True)
        else:
            st.info("Dense không trả về đoạn tài liệu.")
    with bm25_col:
        st.markdown("**BM25 · khớp từ khóa**")
        st.caption("Điểm BM25 chỉ dùng để xếp hạng trong danh sách BM25.")
        if trace.get("bm25"):
            st.dataframe(search_rows(trace["bm25"]), hide_index=True, use_container_width=True)
        else:
            st.info("BM25 không trả về đoạn tài liệu.")

    st.markdown("### 2. Gộp thứ hạng bằng RRF")
    st.caption("RRF(d) = Σ 1 / (60 + hạng). Điểm RRF không so trực tiếp với cosine hoặc BM25.")
    rows = fusion_rows(trace)
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)
    else:
        st.info("Chưa có danh sách RRF để hiển thị.")

    st.markdown("### 3. Quyết định fallback")
    best = float(trace.get("best_dense_score", 0))
    threshold = float(trace.get("score_threshold", 0))
    score_col, threshold_col, decision_col = st.columns(3)
    score_col.metric("Cosine tốt nhất", f"{best:.3f}")
    threshold_col.metric("Ngưỡng cấu hình", f"{threshold:.3f}")
    labels = {
        "hybrid": "Dùng Hybrid + RRF", "dense": "Dùng Dense-only",
        "pageindex": "Dùng PageIndex", "no_results": "Không có kết quả",
        "hybrid_after_empty_fallback": "PageIndex rỗng · giữ Hybrid",
        "hybrid_after_fallback_error": "PageIndex lỗi · giữ Hybrid",
        "dense_after_empty_fallback": "PageIndex rỗng · giữ Dense",
        "dense_after_fallback_error": "PageIndex lỗi · giữ Dense",
    }
    decision_col.metric("Nhánh được chọn", labels.get(trace.get("decision"), "Chưa xác định"))
    if trace.get("fallback_attempted"):
        st.caption("Fallback được kích hoạt từ cosine gốc. Khi PageIndex không có bằng chứng, hệ thống có thể từ chối xác minh.")
    render_sources(trace.get("context_chunks", sources), "4. Đoạn tài liệu đưa vào LLM")
    if trace.get("generation_status") == "cited":
        st.success("5. Câu trả lời có citation khớp với ID đoạn tài liệu.")
    elif trace.get("generation_status") in {"refused", "no_evidence"}:
        st.warning("5. Hệ thống từ chối xác minh vì không có câu trả lời kèm citation hợp lệ.")


def render_evaluation() -> None:
    st.header("Đánh giá A/B trên cùng bộ câu hỏi")
    st.write(
        "Dense-only (A) và Hybrid + RRF (B) dùng cùng corpus, generator, prompt và top_k. "
        "Fallback được tắt trong phép đo này để chỉ còn chiến lược truy xuất là biến thay đổi."
    )
    try:
        golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
        if not isinstance(golden, list):
            raise ValueError("Golden dataset phải là một danh sách")
    except (OSError, ValueError):
        golden = []
        st.warning("Chưa đọc được golden dataset. Kiểm tra file JSON của bộ câu hỏi tham chiếu.")
    st.metric("Câu hỏi tham chiếu", len(golden))
    if golden:
        with st.expander("Xem các câu hỏi tham chiếu"):
            st.dataframe(
                [{"#": index, "Câu hỏi": item.get("question", ""),
                  "Đáp án kỳ vọng": item.get("expected_answer", "")}
                 for index, item in enumerate(golden, 1)],
                hide_index=True, use_container_width=True,
            )
    if not EVALUATION_PATH.exists():
        st.info("Đã có bộ câu hỏi tham chiếu; chưa chạy đánh giá A/B. Chạy `python -m src.evaluate_ab` sau khi xác nhận index và LLM để tạo results.json.")
        return
    try:
        payload = json.loads(EVALUATION_PATH.read_text(encoding="utf-8"))
        summary = payload["summary"]
        cases = payload["cases"]
    except (OSError, ValueError, KeyError, TypeError):
        st.error("File đánh giá không đúng định dạng; cần chạy lại phép đo.")
        return
    st.caption(f"{len(cases)} câu hỏi · corpus: {payload.get('corpus_version', 'chưa ghi')} · ngày chạy: {payload.get('run_at', 'chưa ghi')}")
    table = []
    try:
        for metric in ("faithfulness", "answer_relevance", "context_recall", "context_precision"):
            a, b = float(summary["A"][metric]), float(summary["B"][metric])
            table.append({"Metric": metric.replace("_", " ").title(), "Dense-only": a, "Hybrid + RRF": b, "Δ B−A": b - a})
    except (KeyError, TypeError, ValueError):
        st.error("Kết quả đánh giá thiếu một trong bốn metric cần thiết.")
        return
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.bar_chart(pd.DataFrame(table).set_index("Metric")[["Dense-only", "Hybrid + RRF"]])
    st.subheader("Từng câu hỏi và trường hợp thất bại")
    display_fields = ["config", "question", "faithfulness", "answer_relevance", "context_recall", "context_precision", "latency_seconds"]
    st.dataframe([{field: case.get(field) for field in display_fields} for case in cases], hide_index=True, use_container_width=True)
    metric_fields = ["faithfulness", "answer_relevance", "context_recall", "context_precision"]
    worst = sorted(cases, key=lambda case: sum(float(case.get(field, 0)) for field in metric_fields))[:3]
    st.markdown("**Ba ca có tổng điểm thấp nhất**")
    for case in worst:
        with st.expander(f"Config {case.get('config', '?')} · {case.get('question', '')}"):
            st.write("**Câu trả lời:**", case.get("answer", ""))
            st.write("**Đáp án tham chiếu:**", case.get("expected_answer", ""))
            st.write("**Context tham chiếu:**", case.get("expected_context", ""))
            for index, context in enumerate(case.get("retrieved_contexts", []), 1):
                st.write(f"**Đoạn truy xuất {index}:** {context}")


st.markdown(
    """<div class="hero"><h1>RAG tuyển sinh đại học</h1>
    <p>Đặt câu hỏi · theo dấu từng bước truy xuất · kiểm tra đoạn tài liệu và nguồn của câu trả lời</p></div>""",
    unsafe_allow_html=True,
)
with st.sidebar:
    st.title("Lab 08")
    st.caption("Xây dựng và đánh giá RAG Pipeline")
    top_k = st.slider("Số đoạn tài liệu đưa vào LLM", 1, 10, 5)
    corpus_files = list(STANDARDIZED_DIR.rglob("*.md")) if STANDARDIZED_DIR.exists() else []
    st.metric("Tài liệu đã chuẩn hóa", len(corpus_files))
    if not corpus_files:
        st.warning("Chưa có corpus tuyển sinh. Demo thật hoạt động sau khi dữ liệu được thu thập và index.")
    st.caption("Một trường · một kỳ tuyển sinh · chỉ trả lời theo nguồn đã thu thập")
    with st.expander("Nhật ký xử lý gần đây"):
        st.caption("File log: .cache/rag_demo.log · không ghi API key hoặc nguyên văn câu hỏi")
        render_events(recent_events(30))

overview, demo, evaluation = st.tabs(["Bài toán & pipeline", "Demo từng bước", "Đánh giá A/B"])
with overview:
    st.header("Vì sao cần RAG cho tuyển sinh?")
    st.write(
        "Điều kiện xét tuyển, mốc thời gian và chính sách hỗ trợ thường nằm ở nhiều tài liệu. "
        "Một câu trả lời hữu ích phải chỉ ra đúng đoạn đã dùng, để người hỏi mở nguồn và tự kiểm tra."
    )
    columns = st.columns(4)
    steps = [
        ("01 · Chuẩn hóa", "PDF và trang tuyển sinh → Markdown có metadata nguồn"),
        ("02 · Truy xuất", "Dense tìm theo nghĩa; BM25 tìm mã, tên và từ khóa"),
        ("03 · Chọn bằng chứng", "RRF gộp hạng; cosine gốc quyết định fallback"),
        ("04 · Trả lời", "LLM nhận đoạn tài liệu, gắn citation hoặc từ chối"),
    ]
    for column, (title, description) in zip(columns, steps):
        with column:
            st.markdown(f'<div class="step"><strong>{title}</strong><br>{description}</div>', unsafe_allow_html=True)
    st.info("Các điểm Dense, BM25 và RRF có thang đo khác nhau. Trang demo giữ từng điểm trong đúng giai đoạn của nó.")

with demo:
    st.header("Theo dấu một câu hỏi")
    st.caption("Gợi ý: “Điều kiện xét học bổng là gì?” · “Hồ sơ cần những giấy tờ nào?” · thử một câu ngoài phạm vi tuyển sinh")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "events" in message:
                with st.expander(f"Nhật ký xử lý · {message.get('request_id', '?')}"):
                    render_events(message["events"])
                if message.get("error"):
                    st.error(f"Lỗi kỹ thuật: {message['error']}")
            if message["role"] == "assistant" and "trace" in message:
                with st.expander("Xem toàn bộ pipeline của câu trả lời này"):
                    render_trace(message["trace"], message.get("sources", []))
                render_sources(message.get("sources", []), "Nguồn được trích trong câu trả lời")
    query = st.chat_input("Hỏi về dữ liệu tuyển sinh đã thu thập...")
    if query:
        st.session_state.messages.append({"role": "user", "content": query})
        events: list[dict] = []

        def on_step(event: dict) -> None:
            events.append(event)
            st.write(f"**{event['stage']} · {event['status']}** — {event['message']}")

        try:
            with st.status("Đang chạy pipeline...", expanded=True) as progress:
                result, trace = generate_with_trace(query, top_k=top_k, on_step=on_step)
                progress.update(label="Pipeline đã hoàn tất", state="complete")
            st.session_state.messages.append({
                "role": "assistant", "content": result["answer"],
                "sources": result["sources"], "trace": trace,
                "events": events, "request_id": trace.get("request_id"),
            })
        except Exception as error:
            error_label = safe_error(error)
            request_id = events[0]["request_id"] if events else new_request_id()
            if not events or events[-1].get("status") != "error":
                record_event(events, request_id, "request", "error",
                             "Pipeline dừng do lỗi", error=error_label)
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Không thể chạy truy xuất lúc này. Xem nhật ký xử lý để biết pipeline dừng ở bước nào.",
                "events": events, "request_id": request_id, "error": error_label,
            })
        st.rerun()

with evaluation:
    render_evaluation()
