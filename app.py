"""NEU-inspired landing page and a native Streamlit RAG chat."""

import json

import streamlit as st
from dotenv import load_dotenv

from src.ui_chat import answer_question, configuration_issue
from src.ui_content import ASSETS, ROOT, asset, home_html, icon, source_details

load_dotenv(ROOT / ".env")

st.set_page_config(
    page_title="NEU | Hỏi đáp tuyển sinh",
    page_icon=str(ASSETS / "neu-logo.webp"),
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.html(f"<style>{(ASSETS / 'neu.css').read_text(encoding='utf-8')}</style>")

st.session_state.setdefault("messages", [])
st.session_state.setdefault("view", "chat" if st.query_params.get("view") == "chat" else "home")
st.session_state.setdefault("top_k", 5)
st.session_state.setdefault("pending_question", None)


def navigate(view: str) -> None:
    st.session_state.view = view
    st.query_params["view"] = view


def new_conversation() -> None:
    st.session_state.messages = []
    st.session_state.pending_question = None


def suggest(question: str) -> None:
    st.session_state.pending_question = question


def render_message(message: dict) -> None:
    avatar = str(ASSETS / "neu-logo.webp") if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])
        if message["role"] != "assistant":
            return
        sources = message.get("display_sources", [])
        if sources:
            st.caption("Nguồn tham khảo · Số Document tương ứng với trích dẫn trong câu trả lời")
        for index, source in enumerate(sources, 1):
            title, url = source_details(source)
            with st.expander(f"[Document {index}] {title}"):
                st.markdown(source.get("content", ""))
                if url:
                    st.link_button("Đọc bài viết gốc", url, icon=":material/open_in_new:")
                st.caption(f"Nguồn: {source.get('metadata', {}).get('source', '')}")
        if message.get("status") == "unverified":
            st.caption("Chưa có câu trả lời được xác minh. Có thể thiếu bằng chứng hoặc dịch vụ trả lời đang không khả dụng.")
        with st.expander("Chi tiết truy xuất"):
            st.caption(
                f"Phương thức: {message.get('retrieval_source', 'none')} · "
                f"Thời gian: {message.get('elapsed', 0):.2f}s · {len(sources)} đoạn tài liệu"
            )
            for index, source in enumerate(sources, 1):
                st.caption(
                    f"Document {index} · {source.get('retrieval_method', '')} · "
                    f"Score: {float(source.get('score', 0)):.4f} · ID: {source.get('id', '')}"
                )
            if sources:
                st.caption("Score là điểm truy xuất, không phải xác suất câu trả lời đúng. Điểm RRF và cosine có thang đo khác nhau.")


def render_chat() -> None:
    with st.container(key="chat_shell"):
        left, right = st.columns([1, 1])
        with left:
            st.button("Trang chủ", icon=":material/arrow_back:", key="back_home", on_click=navigate, args=("home",))
        with right:
            st.button("Cuộc trò chuyện mới", icon=":material/edit_square:", key="new_chat", on_click=new_conversation)
        st.html(f"""<div class="chat-brand"><div class="chat-brand-left"><img src="{asset('neu-logo.webp')}" alt="NEU 70 năm"><div><strong>Trợ lý tuyển sinh NEU</strong><span>Đại học Kinh tế Quốc dân</span></div></div><span class="chat-badge">DEMO HỌC PHẦN</span></div>""")

        if not st.session_state.messages:
            st.html(f"""<div class="chat-intro"><div class="intro-icon">{icon('chat')}</div><h1>Chào bạn, mình có thể giúp gì?</h1><p>Cùng tìm hiểu tuyển sinh NEU qua tài liệu và thông báo.<br>Mỗi câu trả lời có nguồn để bạn kiểm chứng.</p></div>""")
            questions = [
                "NEU năm 2026 có những phương thức xét tuyển nào?",
                "Điều kiện xét tuyển kết hợp năm 2026 là gì?",
                "Cần chuẩn bị hồ sơ đăng ký xét tuyển như thế nào?",
                "Quy định tuyển sinh liên thông năm 2026 là gì?",
            ]
            with st.container(key="suggestions"):
                for row in range(2):
                    columns = st.columns(2)
                    for index, (column, question) in enumerate(zip(columns, questions[row * 2:row * 2 + 2])):
                        with column:
                            st.button(question, key=f"suggestion_{row}_{index}", on_click=suggest, args=(question,), use_container_width=True)

        issue = configuration_issue()
        if issue:
            st.info(issue, icon=":material/info:")
        with st.expander("Tùy chọn hội thoại", icon=":material/tune:"):
            st.slider("Số đoạn tài liệu tham khảo", min_value=3, max_value=10, key="top_k")
            st.caption("Hội thoại được giữ trong phiên trình duyệt này. Mỗi câu hỏi được tra cứu độc lập; hãy ghi rõ năm tuyển sinh và nội dung cần hỏi.")
            if st.session_state.messages:
                st.download_button(
                    "Tải hội thoại (.json)",
                    json.dumps(st.session_state.messages, ensure_ascii=False, indent=2),
                    file_name="neu-hoi-thoai.json",
                    mime="application/json",
                    icon=":material/download:",
                )

        for message in st.session_state.messages:
            render_message(message)

        query = st.chat_input("Nhập câu hỏi tuyển sinh của bạn…", max_chars=2000)
        pending = st.session_state.pop("pending_question", None)
        query = (query or pending or "").strip()
        if query:
            user_message = {"role": "user", "content": query}
            st.session_state.messages.append(user_message)
            render_message(user_message)
            with st.spinner("Đang tìm thông tin trong tài liệu tuyển sinh…"):
                response = answer_question(query, st.session_state.top_k)
            st.session_state.messages.append(response)
            st.rerun()
        st.html('<p class="chat-disclaimer">Demo học phần · Trợ lý có thể nhầm lẫn. Hãy đối chiếu nguồn và thông báo chính thức của NEU.</p>')


if st.session_state.view == "chat":
    render_chat()
else:
    st.html(home_html())
    st.button(
        "Hỏi đáp tuyển sinh",
        icon=":material/chat_bubble_outline:",
        key="chat_launcher",
        on_click=navigate,
        args=("chat",),
    )
