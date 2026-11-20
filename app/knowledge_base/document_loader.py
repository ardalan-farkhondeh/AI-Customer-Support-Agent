
import logging
from pathlib import Path

from pypdf import PdfReader

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt"}


def load_documents(directory="data/documents"):
    documents = []
    directory = Path(directory)

    directory.mkdir(parents=True, exist_ok=True)

    for file_path in sorted(directory.rglob("*")):

        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()

        if extension not in SUPPORTED_EXTENSIONS:
            continue

        try:
            if extension == ".pdf":
                reader = PdfReader(str(file_path))

                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

            else:
                text = file_path.read_text(
                    encoding="utf-8-sig",
                    errors="replace"
                )

            text = text.strip()

            if not text:
                logger.warning(
                    "Document contains no extractable text: %s",
                    file_path
                )
                continue

            documents.append({
                "text": text,
                "metadata": {
                    "source": file_path.name,
                    "file_type": extension
                }
            })

            logger.info("Loaded document: %s", file_path.name)

        except Exception:
            logger.exception(
                "Failed to load document: %s",
                file_path
            )

    logger.info("Total documents loaded: %s", len(documents))

    return documents
