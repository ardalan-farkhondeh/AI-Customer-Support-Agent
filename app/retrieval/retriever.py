
import logging

from app.knowledge_base.vector_store import search_documents

logger = logging.getLogger(__name__)


def retrieve_context(
    query: str,
    n_results: int = 3,
) -> dict:

    if not isinstance(query, str) or not query.strip():
        return {
            "query": "",
            "context": "",
            "sources": [],
        }

    if not isinstance(n_results, int) or n_results < 1:
        raise ValueError("n_results must be a positive integer.")

    query = query.strip()

    try:
        results = search_documents(
            query,
            n_results=n_results,
        )

        if not isinstance(results, list):
            raise RuntimeError(
                "Invalid vector search response."
            )

        context_parts = []
        sources = []

        for item in results:

            if not isinstance(item, dict):
                continue

            text = item.get("text", "")

            if not isinstance(text, str) or not text.strip():
                continue

            context_parts.append(text.strip())

            metadata = item.get("metadata") or {}

            if not isinstance(metadata, dict):
                metadata = {}

            source = metadata.get("source", "unknown")

            if source not in sources:
                sources.append(source)

        return {
            "query": query,
            "context": "\n\n".join(context_parts),
            "sources": sources,
        }

    except Exception as exc:
        logger.exception(
            "Knowledge-base retrieval failed."
        )

        raise RuntimeError(
            "Knowledge-base retrieval failed."
        ) from exc
