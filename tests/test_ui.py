"""Offline UI integration: real generation/reordering with mocked retrieval/LLM."""

import importlib.util
import sys
import types
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.ui_chat import answer_question
from src.ui_content import safe_url, source_details

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def runtime(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-key")
    chunks = [
        {"id": f"chunk-{i}", "content": f"Evidence {i}", "score": 1 - i / 10,
         "metadata": {"title": f"Title {i}", "source": f"source-{i}.md", "url": None, "doc_type": "legal", "chunk_index": i},
         "retrieval_method": "hybrid"}
        for i in range(5)
    ]
    calls = []
    retrieval = types.ModuleType("src.task9_retrieval_pipeline")

    def retrieve(query, top_k):
        calls.append((query, top_k))
        return chunks[:top_k]

    retrieval.retrieve = retrieve
    monkeypatch.setitem(sys.modules, "src.task9_retrieval_pipeline", retrieval)
    spec = importlib.util.spec_from_file_location("src.task10_generation", ROOT / "src" / "task10_generation.py")
    generation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generation)
    monkeypatch.setattr(generation, "call_llm", lambda *args: "Câu trả lời kiểm thử [Document 2].")
    monkeypatch.setitem(sys.modules, "src.task10_generation", generation)
    return calls, generation


def open_chat():
    app = AppTest.from_file(str(ROOT / "app.py")).run(timeout=15)
    assert not app.exception
    app.button(key="chat_launcher").click().run()
    assert not app.exception
    return app


def test_chat_keeps_history_and_sources_across_navigation_and_rerun(runtime):
    calls, _ = runtime
    app = open_chat()
    app.chat_input[0].set_value("Điều kiện tuyển sinh?").run(timeout=15)
    assert not app.exception
    assert calls == [("Điều kiện tuyển sinh?", 5)]
    assert len(app.session_state.messages) == 2
    assert len(app.chat_message) == 2
    source_labels = [item.label for item in app.expander if item.label.startswith("[Document")]
    assert source_labels[1] == "[Document 2] Title 2"
    app.run()
    assert len(calls) == 1
    app.button(key="back_home").click().run()
    app.button(key="chat_launcher").click().run()
    assert len(app.chat_message) == 2
    assert len(calls) == 1
    app.button(key="new_chat").click().run()
    assert app.session_state.messages == []
    assert len(app.chat_message) == 0


def test_suggestion_and_top_k_use_real_adapter(runtime):
    calls, _ = runtime
    app = open_chat()
    app.slider(key="top_k").set_value(3).run()
    app.button(key="suggestion_0_0").click().run(timeout=15)
    assert not app.exception
    assert calls == [("NEU năm 2026 có những phương thức xét tuyển nào?", 3)]
    assert len(app.session_state.messages[1]["sources"]) == 3
    app.run()
    assert len(calls) == 1


def test_missing_key_is_explicit_and_does_not_call_runtime(runtime, monkeypatch):
    calls, _ = runtime
    monkeypatch.delenv("OPENAI_API_KEY")
    app = open_chat()
    assert app.info
    app.chat_input[0].set_value("Xin chào").run(timeout=15)
    assert not app.exception
    assert calls == []
    assert app.session_state.messages[-1]["status"] == "unavailable"


def test_retrieval_failure_preserves_turn_without_crash(runtime, monkeypatch):
    _, generation = runtime

    def fail(*args, **kwargs):
        raise RuntimeError("offline provider failure")

    monkeypatch.setattr(generation, "retrieve", fail)
    app = open_chat()
    app.chat_input[0].set_value("Hồ sơ xét tuyển?").run(timeout=15)
    assert not app.exception
    assert len(app.session_state.messages) == 2
    assert app.session_state.messages[-1]["status"] == "error"
    assert "offline provider failure" not in app.session_state.messages[-1]["content"]


def test_citation_order_matches_actual_generation_context(runtime):
    _, generation = runtime
    prompts = []
    generation.call_llm = lambda system, context: prompts.append(context) or "Answer [Document 2]"
    response = answer_question("Question", 5)
    assert "[Document 2 | Title: Title 2" in prompts[0]
    assert response["display_sources"][1]["id"] == "chunk-2"
    assert [source["id"] for source in response["sources"]] == [f"chunk-{i}" for i in range(5)]


def test_original_news_url_is_recovered_and_unsafe_links_rejected():
    title, url = source_details({"metadata": {"source": "article_01.md", "title": "article_01", "url": None}})
    assert title != "article_01"
    assert url.startswith("https://neu.edu.vn/")
    assert safe_url("javascript:alert(1)") is None
    assert safe_url("file:///etc/passwd") is None
