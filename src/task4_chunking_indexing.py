"""
Task 4 — Chunking, embedding và indexing.

Hướng dẫn:
    1. Đọc toàn bộ Markdown trong data/standardized/.
    2. Chia văn bản bằng strategy đã chọn.
    3. Embed chunks bằng một provider duy nhất.
    4. Upsert vào ChromaDB với cosine distance.

Mỗi document/chunk phải theo docs/MODULE_CONTRACTS.md. ID cần ổn định để
chạy lại pipeline không tạo dữ liệu trùng. Task 5 phải dùng chung embed_texts().
"""

import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers").strip().lower()


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_DIM = max(1, int(os.getenv("EMBEDDING_DIM", "1024")))

EMBEDDING_BATCH_SIZE = max(1, int(os.getenv("EMBEDDING_BATCH_SIZE", "32")))
INDEX_BATCH_SIZE = max(1, int(os.getenv("INDEX_BATCH_SIZE", "500")))

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Dispatch theo EMBEDDING_PROVIDER trong .env."""
    if not texts:
        return []
    if EMBEDDING_PROVIDER == "openai":
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("EMBEDDING_MODEL") or "text-embedding-3-small"
        options = {"input": texts, "model": model}
        if model.startswith("text-embedding-3"):
            options["dimensions"] = EMBEDDING_DIM
        response = client.embeddings.create(**options)
        return [item.embedding for item in response.data]
    elif EMBEDDING_PROVIDER == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        model = os.getenv("EMBEDDING_MODEL") or "gemini-embedding-001"
        try:
            response = client.models.embed_content(
                model=model,
                contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
            )
            return [embedding.values for embedding in response.embeddings]
        finally:
            client.close()
    elif EMBEDDING_PROVIDER == "sentence_transformers":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        return model.encode(texts).tolist()
    raise ValueError(
        f"Unsupported EMBEDDING_PROVIDER={EMBEDDING_PROVIDER!r}. "
        "Use sentence_transformers, openai, or gemini."
    )


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _markdown_metadata(path: Path, content: str) -> dict:
    """Recover the title and optional source URL written by Task 3."""
    title_match = re.search(r"^#\s+(.+?)\s*$", content, flags=re.MULTILINE)
    source_match = re.search(r"^\*\*Source:\*\*\s*(\S+)\s*$", content, flags=re.MULTILINE)
    return {
        "source": path.name,
        "title": title_match.group(1).strip() if title_match else path.stem,
        "url": source_match.group(1).strip() if source_match else None,
    }


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    documents = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        doc_type = "legal" if "legal" in path.parts else "news"
        metadata = _markdown_metadata(path, content)
        documents.append({
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": content,
            "metadata": {
                **metadata,
                "doc_type": doc_type,
            },
        })
    return documents
    # raise NotImplementedError("Implement load_documents")


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        for index, text in enumerate(_split_text(document["content"])):
            chunks.append({
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {**document["metadata"], "chunk_index": index},
            })
    return chunks


def _split_text(text: str) -> list[str]:
    """Split text without importing the embedding stack."""
    if not text:
        return []

    separators = ("\n\n", "\n", ". ", " ")
    chunks: list[str] = []
    start = 0

    while start < len(text):
        limit = min(start + CHUNK_SIZE, len(text))
        boundaries = [
            text.rfind(separator, start, limit) + len(separator)
            for separator in separators
            if text.rfind(separator, start, limit) >= start
        ]
        end = max(boundaries, default=limit)
        chunks.append(text[start:end])

        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)

    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Thêm embedding vào từng chunk."""
    embedded = []
    vector_dimension = None
    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        batch = chunks[start:start + EMBEDDING_BATCH_SIZE]
        vectors = embed_texts([chunk["content"] for chunk in batch])
        if len(vectors) != len(batch):
            raise ValueError(
                f"Embedding provider returned {len(vectors)} vectors for "
                f"{len(batch)} texts"
            )
        for chunk, vector in zip(batch, vectors):
            if not vector:
                raise ValueError(f"Empty embedding for chunk {chunk['id']}")
            if len(vector) != EMBEDDING_DIM:
                raise ValueError(
                    f"Embedding dimension for chunk {chunk['id']} must be "
                    f"{EMBEDDING_DIM}, got {len(vector)}"
                )
            if vector_dimension is None:
                vector_dimension = len(vector)
            elif len(vector) != vector_dimension:
                raise ValueError(
                    f"Inconsistent embedding dimension for chunk {chunk['id']}: "
                    f"expected {vector_dimension}, got {len(vector)}"
                )
            embedded.append({**chunk, "embedding": vector})
    return embedded


def _chroma_metadata(metadata: dict) -> dict:
    """Chroma metadata values cannot be None; retain the required URL field."""
    return {key: "" if value is None else value for key, value in metadata.items()}


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    if not chunks:
        raise ValueError("No chunks to index; refusing to clear the existing collection")
    chunk_ids = [chunk["id"] for chunk in chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Chunk IDs must be unique before indexing")

    collection = get_collection()
    new_ids = set(chunk_ids)
    existing_ids = set(collection.get(include=[]).get("ids", []))
    stale_ids = sorted(existing_ids - new_ids)
    if stale_ids:
        collection.delete(ids=stale_ids)

    for start in range(0, len(chunks), INDEX_BATCH_SIZE):
        batch = chunks[start:start + INDEX_BATCH_SIZE]
        collection.upsert(
            ids=[chunk["id"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            metadatas=[_chroma_metadata(chunk["metadata"]) for chunk in batch],
        )


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
