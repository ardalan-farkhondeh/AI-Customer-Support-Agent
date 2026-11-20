
import hashlib
import logging
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

logger = logging.getLogger(__name__)

# =========================
# Configuration
# =========================

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "customer_support_knowledge"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# =========================
# ChromaDB Initialization
# =========================

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL,
    device="cpu"
)

client = chromadb.PersistentClient(
    path=str(DB_PATH)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"}
)


# =========================
# Add Documents
# =========================

def add_documents(
    chunks: list[str],
    metadata: dict
) -> int:

    if not chunks:
        return 0

    source = str(metadata.get("source", "unknown"))

    ids = []
    documents = []
    metadatas = []

    for index, chunk in enumerate(chunks):

        if not isinstance(chunk, str):
            continue

        chunk = chunk.strip()

        if not chunk:
            continue

        document_id = hashlib.sha256(
            f"{source}:{index}:{chunk}".encode("utf-8")
        ).hexdigest()

        ids.append(document_id)
        documents.append(chunk)

        metadatas.append({
            **metadata,
            "source": source,
            "chunk_index": index
        })

    if not documents:
        return 0

    try:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        logger.info(
            "Stored %s chunks from %s",
            len(documents),
            source
        )

        return len(documents)

    except Exception:
        logger.exception(
            "Failed to store documents from %s",
            source
        )
        raise


# =========================
# Search Documents
# =========================

def search_documents(
    query: str,
    n_results: int = 3
) -> list[dict]:

    if not isinstance(query, str) or not query.strip():
        return []

    if n_results < 1:
        return []

    try:
        total = collection.count()

        if total == 0:
            return []

        result = collection.query(
            query_texts=[query.strip()],
            n_results=min(n_results, total),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        MAX_DISTANCE = 0.65

        return [
            {
                "text": document,
                "metadata": metadata or {},
                "distance": distance
            }
            for document, metadata, distance in zip(
                documents,
                metadatas,
                distances
            )
            if document and distance is not None
            and distance <= MAX_DISTANCE
        ]

    except Exception:
        logger.exception("Document search failed")
        raise
