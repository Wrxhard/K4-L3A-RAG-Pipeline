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

from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")


STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Giải thích lựa chọn tham số trong báo cáo nhóm.
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIM = 1024

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Dispatch theo EMBEDDING_PROVIDER trong .env."""
    if EMBEDDING_PROVIDER == "openai":
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        response = client.embeddings.create(input=texts, model=model)
        return [item.embedding for item in response.data]
    elif EMBEDDING_PROVIDER == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
        result = genai.embed_content(model=model, content=texts)
        return result["embedding"] if isinstance(texts, str) else [r for r in result["embedding"]]
    else:  # sentence_transformers (local)
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(EMBEDDING_MODEL)
        return model.encode(texts).tolist()


def get_collection():
    """Mở Chroma collection dùng cosine distance."""
    # TODO: Tạo hoặc mở persistent collection.
    #
    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Đọc Markdown và trả về danh sách Document."""
    # TODO: Đọc mọi .md và tạo Document theo contract.
    #
    documents = []
    for path in STANDARDIZED_DIR.rglob("*.md"):
        doc_type = "legal" if "legal" in path.parts else "news"
        documents.append({
            "id": path.relative_to(STANDARDIZED_DIR).as_posix(),
            "content": path.read_text(encoding="utf-8"),
            "metadata": {
                "source": path.name,
                "title": path.stem,
                "doc_type": doc_type,
                "url": None,
            },
        })
    return documents
    # raise NotImplementedError("Implement load_documents")


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thành chunks có id và chunk_index."""
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
    # TODO: Embed theo batch và giữ nguyên các field của chunk.
    #
    vectors = embed_texts([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        chunk["embedding"] = vector
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vào ChromaDB."""
    # TODO: Upsert ids, documents, embeddings và metadatas.
    #
    collection = get_collection()
    collection.upsert(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )
    # raise NotImplementedError("Implement index_to_vectorstore")


def run_pipeline() -> None:
    """Chạy load, chunk, embed và index."""
    documents = load_documents()
    chunks = chunk_documents(documents)
    embedded_chunks = embed_chunks(chunks)
    index_to_vectorstore(embedded_chunks)
    print(f"Indexed {len(embedded_chunks)} chunks")


if __name__ == "__main__":
    run_pipeline()
