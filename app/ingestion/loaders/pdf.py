
from pathlib import Path

import logfire
from pypdf import PdfReader


def parse_pdf_pages(
    file_path: str,
    password: str | None = None,
) -> list[dict]:
    """
    Extract text from a PDF page by page.

    Returns:
        List of dictionaries containing page content and metadata.
    """

    path = Path(file_path)

    with logfire.span("PDF Parsing", file_path=str(path)):

        try:
            # 1. Validate file
            if not path.exists():
                raise FileNotFoundError(
                    f"PDF file not found: {path}"
                )

            if not path.is_file():
                raise ValueError("Provided path is not a file")

            # 2. Load PDF
            reader = PdfReader(str(path))

            # 3. Handle encrypted PDFs
            if reader.is_encrypted:
                if not password:
                    raise ValueError(
                        "PDF is encrypted. Password required."
                    )

                if not reader.decrypt(password):
                    raise ValueError("Incorrect PDF password")

            num_pages = len(reader.pages)

            if num_pages == 0:
                raise ValueError("PDF contains no pages")

            logfire.info(
                "PDF loaded successfully",
                total_pages=num_pages,
                file_name=path.name
            )

            # 4. Extract text page by page
            documents = []

            for page_num, page in enumerate(reader.pages, start=1):

                with logfire.span(
                    "Extracting PDF page",
                    page_number=page_num
                ):

                    text = page.extract_text() or ""
                    text = text.strip()

                    if not text:
                        logfire.warning(
                            "Empty page detected",
                            page_number=page_num
                        )
                        continue

                    documents.append({
                        "page_content": text,
                        "metadata": {
                            "source": path.name,
                            "file_path": str(path),
                            "page": page_num,
                            "total_pages": num_pages,
                        }
                    })

            # 5. Validate extraction
            if not documents:
                logfire.warning(
                    "No extractable text found in PDF. "
                    "It may be a scanned document requiring OCR.",
                    file_name=path.name,
                )
                return []

            total_characters = sum(
                len(doc["page_content"]) for doc in documents
            )

            logfire.info(
                "PDF parsing completed",
                extracted_pages=len(documents),
                total_pages=num_pages,
                total_characters=total_characters
            )

            return documents

        except Exception as e:
            logfire.error(
                "PDF parsing failed",
                file_path=str(path),
                error=str(e)
            )
            raise


def parse_pdf(file_path: str) -> str:
    """
    Backward-compatible function returning plain text.

    Returns an empty string when the PDF cannot be read or has no extractable
    text (e.g. scanned documents), so callers can skip gracefully.
    """
    try:
        pages = parse_pdf_pages(file_path)
        return "\n\n".join(doc["page_content"] for doc in pages)
    except Exception as e:
        logfire.error(
            "PDF parsing failed",
            file_path=file_path,
            error=str(e),
        )
        return ""
