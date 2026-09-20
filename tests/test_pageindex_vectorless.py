import json

from src.contracts import validate_search_results


def test_upload_documents_caches_document_ids(monkeypatch, tmp_path):
    import src.task8_pageindex_vectorless as pageindex

    standardized = tmp_path / "standardized" / "news"
    standardized.mkdir(parents=True)
    article = standardized / "article.md"
    article.write_text("NEU admissions content", encoding="utf-8")
    cache_path = tmp_path / "pageindex_cache.json"

    class FakeClient:
        def __init__(self, api_key):
            assert api_key == "test-key"

        def submit_document(self, file_path):
            assert file_path.endswith(".pdf")
            return {"doc_id": "doc-article"}

    monkeypatch.setattr(pageindex, "PAGEINDEX_API_KEY", "test-key")
    monkeypatch.setattr(pageindex, "STANDARDIZED_DIR", tmp_path / "standardized")
    monkeypatch.setattr(pageindex, "CACHE_FILE", cache_path)
    monkeypatch.setattr(pageindex, "PageIndexClient", FakeClient)

    pageindex.upload_documents()

    assert json.loads(cache_path.read_text(encoding="utf-8")) == {
        "news/article.md": "doc-article"
    }


def test_pageindex_search_parses_retrieval_nodes(monkeypatch, tmp_path):
    import src.task8_pageindex_vectorless as pageindex

    cache_path = tmp_path / "pageindex_cache.json"
    cache_path.write_text(
        json.dumps({"news/article.md": "doc-article"}), encoding="utf-8"
    )

    class FakeClient:
        def __init__(self, api_key):
            pass

        def submit_query(self, doc_id, query, thinking=False):
            assert (doc_id, query, thinking) == ("doc-article", "tuition", False)
            return {"retrieval_id": "retrieval-1"}

        def get_retrieval(self, retrieval_id):
            assert retrieval_id == "retrieval-1"
            return {
                "status": "completed",
                "results": [
                    {"id": "node-2", "text": "Tuition is paid per semester.", "page": 2, "score": 0.8},
                    {"id": "node-3", "text": "Scholarships are available.", "page": 3, "score": 0.5},
                ],
            }

    monkeypatch.setattr(pageindex, "PAGEINDEX_API_KEY", "test-key")
    monkeypatch.setattr(pageindex, "CACHE_FILE", cache_path)
    monkeypatch.setattr(pageindex, "PageIndexClient", FakeClient)
    monkeypatch.setattr(pageindex, "POLL_INTERVAL_SECONDS", 0)

    output = pageindex.pageindex_search("tuition", top_k=1)

    validate_search_results(output, top_k=1, expected_method="pageindex")
    assert len(output) == 1
    assert output[0]["content"] == "Tuition is paid per semester."
    assert output[0]["metadata"]["source"] == "news/article.md"
    assert output[0]["metadata"]["doc_type"] == "news"
    assert output[0]["metadata"]["chunk_index"] == 2


def test_pageindex_search_returns_empty_when_provider_fails(monkeypatch, tmp_path):
    import src.task8_pageindex_vectorless as pageindex

    cache_path = tmp_path / "pageindex_cache.json"
    cache_path.write_text(json.dumps({"legal/policy.md": "doc-policy"}), encoding="utf-8")

    class BrokenClient:
        def __init__(self, api_key):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(pageindex, "PAGEINDEX_API_KEY", "test-key")
    monkeypatch.setattr(pageindex, "CACHE_FILE", cache_path)
    monkeypatch.setattr(pageindex, "PageIndexClient", BrokenClient)

    assert pageindex.pageindex_search("policy") == []
