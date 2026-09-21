"""Small UI adapter around the existing RAG pipeline."""

import logging
import os
import time

LOGGER = logging.getLogger(__name__)
KEYS = {"openai": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY", "anthropic": "ANTHROPIC_API_KEY"}


def configuration_issue() -> str | None:
    provider = os.getenv("LLM_PROVIDER", "openai")
    key = KEYS.get(provider)
    if key is None:
        return "Nhà cung cấp mô hình chưa được cấu hình hợp lệ."
    if not os.getenv(key, "").strip():
        return "Trợ lý chưa được kết nối với dịch vụ trả lời. Bạn vẫn có thể xem các thông báo trên trang chủ."
    return None


def answer_question(query: str, top_k: int) -> dict:
    """Preserve real pipeline output, with an explicit UI status on failure."""
    started = time.monotonic()
    result = {"role": "assistant", "sources": [], "display_sources": [], "retrieval_source": "none"}
    issue = configuration_issue()
    if issue:
        return {**result, "content": issue, "status": "unavailable", "elapsed": 0.0}
    try:
        # Lazy imports keep the landing page usable before RAG dependencies are installed.
        from .task10_generation import generate_with_citation, reorder_for_llm

        generated = generate_with_citation(query, top_k=top_k)
        answer = generated.get("answer", "")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Pipeline returned an empty answer")
        sources = generated.get("sources", [])
        result.update(
            content=answer,
            sources=sources,
            # Task 10 numbers Document N after reordering, but returns ranked sources.
            # Use the same helper to display those labels without changing its contract.
            display_sources=reorder_for_llm(sources),
            retrieval_source=generated.get("retrieval_source", "none"),
            status="answered" if sources else "unverified",
        )
    except Exception:
        LOGGER.exception("RAG request failed")
        result.update(
            content="Trợ lý hiện chưa thể xử lý câu hỏi này. Bạn vui lòng thử lại sau hoặc tra cứu thông báo trên website NEU.",
            status="error",
        )
    result["elapsed"] = round(time.monotonic() - started, 2)
    return result
