
from pathlib import Path

import logfire
from unstructured.partition.auto import partition


SUPPORTED_EXTENSIONS = {".docx", ".pptx"}


def parse_office(file_path: str) -> list[dict]:
    """
    Parse Office documents (.docx, .pptx)
    using Unstructured.

    Returns structured content with metadata.
    """

    path = Path(file_path)

    with logfire.span(
        "Office Document Parsing",
        filename=str(path)
    ):
        try:
            # 1. Validate file
            if not path.exists():
                raise FileNotFoundError(
                    f"File not found: {path}"
                )

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file format: {path.suffix}"
                )

            # 2. Partition document
            elements = partition(
                filename=str(path)
            )

            documents = []

            # 3. Extract text and metadata
            for element in elements:

                text = str(element).strip()

                if not text:
                    continue

                metadata = element.metadata

                documents.append({
                    "page_content": text,
                    "metadata": {
                        "source": path.name,
                        "file_path": str(path),
                        "category": getattr(
                            element, "category", None
                        ),
                        "page": getattr(
                            metadata, "page_number", None
                        ),
                    }
                })

            # 4. Validate extracted content
            if not documents:
                raise ValueError(
                    f"No text extracted from {path.name}"
                )

            total_chars = sum(
                len(doc["page_content"])
                for doc in documents
            )

            logfire.info(
                "Office document parsed successfully",
                filename=path.name,
                elements=len(documents),
                characters=total_chars
            )

            return documents

        except Exception as e:
            logfire.error(
                "Office document parsing failed",
                filename=str(path),
                error=str(e)
            )
            raise
