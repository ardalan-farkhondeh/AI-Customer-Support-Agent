
import logging

from app.knowledge_base.document_loader import load_documents
from app.knowledge_base.text_splitter import split_text
from app.knowledge_base.vector_store import (
    add_documents,
    search_documents
)

logger = logging.getLogger(__name__)


def ingest_documents(directory="data/documents"):
    documents = load_documents(directory)

    total_chunks = 0
    processed_files = 0
    failed_files = []

    for document in documents:
        try:
            chunks = split_text(document["text"])

            if not chunks:
                continue

            count = add_documents(
                chunks,
                document["metadata"]
            )

            total_chunks += count
            processed_files += 1

        except Exception:
            source = document.get("metadata", {}).get(
                "source", "unknown"
            )

            failed_files.append(source)

            logger.exception(
                "Failed to ingest document: %s",
                source
            )

    return {
        "files_processed": processed_files,
        "chunks_stored": total_chunks,
        "failed_files": failed_files
    }


def retrieve_context(query: str, n_results: int = 3) -> dict:
    query = query.strip()

    if not query:
        return {
            "query": query,
            "context": "",
            "sources": []
        }

    try:
        results = search_documents(
            query,
            n_results=n_results
        )

        context_parts = []
        sources = []

        for result in results:
            text = result.get("text", "").strip()

            if not text:
                continue

            context_parts.append(text)

            metadata = result.get("metadata") or {}
            source = metadata.get("source", "unknown")

            if source not in sources:
                sources.append(source)

        return {
            "query": query,
            "context": "\n\n".join(context_parts),
            "sources": sources
        }

    except Exception:
        logger.exception("Knowledge retrieval failed")

        return {
            "query": query,
            "context": "",
            "sources": []
        }
