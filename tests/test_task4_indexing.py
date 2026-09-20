"""Focused, offline tests for Task 4 data preservation and indexing."""


def test_load_documents_recovers_news_metadata_and_skips_empty(monkeypatch, tmp_path):
    import src.task4_chunking_indexing as task4

    news = tmp_path / "news"
    legal = tmp_path / "legal"
    news.mkdir()
    legal.mkdir()
    (news / "article.md").write_text(
        "# Thông báo tuyển sinh\n\n"
        "**Source:** https://neu.edu.vn/thong-bao/\n\n"
        "**Crawled:** 2026-09-20\n\n---\n\nNội dung tuyển sinh.",
        encoding="utf-8",
    )
    (legal / "policy.md").write_text("# Quy chế tuyển sinh\n\nNội dung.", encoding="utf-8")
    (legal / "empty.md").write_text("  \n", encoding="utf-8")
    monkeypatch.setattr(task4, "STANDARDIZED_DIR", tmp_path)

    documents = task4.load_documents()

    assert [item["id"] for item in documents] == ["legal/policy.md", "news/article.md"]
    news_document = documents[1]
    assert news_document["metadata"] == {
        "source": "article.md",
        "title": "Thông báo tuyển sinh",
        "url": "https://neu.edu.vn/thong-bao/",
        "doc_type": "news",
    }


def test_embed_chunks_batches_and_rejects_missing_vectors(monkeypatch):
    import src.task4_chunking_indexing as task4

    chunks = [
        {"id": f"chunk-{index}", "content": f"text {index}", "metadata": {}}
        for index in range(5)
    ]
    calls = []
    monkeypatch.setattr(task4, "EMBEDDING_BATCH_SIZE", 2)
    monkeypatch.setattr(task4, "EMBEDDING_DIM", 1)

    def embed(texts):
        calls.append(texts)
        return [[float(len(text))] for text in texts]

    monkeypatch.setattr(task4, "embed_texts", embed)
    embedded = task4.embed_chunks(chunks)

    assert [len(batch) for batch in calls] == [2, 2, 1]
    assert all("embedding" not in chunk for chunk in chunks)
    assert [chunk["embedding"] for chunk in embedded] == [[6.0]] * 5

    monkeypatch.setattr(task4, "embed_texts", lambda texts: [])
    try:
        task4.embed_chunks(chunks[:1])
    except ValueError as error:
        assert "returned 0 vectors for 1 texts" in str(error)
    else:
        raise AssertionError("Missing embeddings must fail before indexing")

    monkeypatch.setattr(task4, "EMBEDDING_BATCH_SIZE", 2)
    monkeypatch.setattr(task4, "embed_texts", lambda texts: [[1.0], [1.0, 2.0]][:len(texts)])
    try:
        task4.embed_chunks(chunks[:2])
    except ValueError as error:
        assert "must be 1, got 2" in str(error)
    else:
        raise AssertionError("Mixed embedding dimensions must fail before indexing")


def test_index_upserts_in_batches_and_removes_stale_ids(monkeypatch):
    import src.task4_chunking_indexing as task4

    class FakeCollection:
        def __init__(self):
            self.deleted = []
            self.batches = []

        def get(self, **kwargs):
            assert kwargs == {"include": []}
            return {"ids": ["stale", "chunk-0"]}

        def delete(self, *, ids):
            self.deleted.extend(ids)

        def upsert(self, **kwargs):
            self.batches.append(kwargs)

    collection = FakeCollection()
    chunks = [
        {
            "id": f"chunk-{index}",
            "content": f"text {index}",
            "embedding": [float(index), 1.0],
            "metadata": {"source": "policy.md", "title": "Policy", "doc_type": "legal", "url": None, "chunk_index": index},
        }
        for index in range(3)
    ]
    monkeypatch.setattr(task4, "INDEX_BATCH_SIZE", 2)
    monkeypatch.setattr(task4, "get_collection", lambda: collection)

    task4.index_to_vectorstore(chunks)

    assert collection.deleted == ["stale"]
    assert [len(batch["ids"]) for batch in collection.batches] == [2, 1]
    assert collection.batches[0]["metadatas"][0]["url"] == ""


def test_index_refuses_empty_or_duplicate_input(monkeypatch):
    import src.task4_chunking_indexing as task4

    monkeypatch.setattr(task4, "get_collection", lambda: (_ for _ in ()).throw(AssertionError("must not open Chroma")))
    for invalid, message in (([], "No chunks"), ([{"id": "same"}, {"id": "same"}], "unique")):
        try:
            task4.index_to_vectorstore(invalid)
        except ValueError as error:
            assert message in str(error)
        else:
            raise AssertionError("Invalid input must fail before opening Chroma")
