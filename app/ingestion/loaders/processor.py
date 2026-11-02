
import os
import sys
import uuid
import json
import shutil
import logfire

from qdrant_client import QdrantClient
from qdrant_client.http import models

# Import local modules
from app.config import settings
from app.services.retrieval.embeddings import embed_texts
from app.ingestion.loaders.html import parse_html
from app.ingestion.loaders.pdf import parse_pdf
from app.ingestion.loaders.text import parse_text
from app.ingestion.chunking.splittter import chunk_text

logfire.configure(service_name="enterprise-ingestion-service")

# Initialize Qdrant
qdrant = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY,
    timeout=120
)

# Local storage directories
BASE_STORAGE = "data"

RAW_DIR = os.path.join(BASE_STORAGE, "raw")
PROCESSED_DIR = os.path.join(BASE_STORAGE, "processed")


def save_raw_file(file_path: str, source_type: str):
    """Save original document to local storage."""

    destination_dir = os.path.join(RAW_DIR, source_type)
    os.makedirs(destination_dir, exist_ok=True)

    destination_path = os.path.join(
        destination_dir,
        os.path.basename(file_path)
    )

    shutil.copy2(file_path, destination_path)

    return destination_path


def save_processed_data(data, filename: str, source_type: str):
    """Save processed chunks as JSON locally."""

    destination_dir = os.path.join(PROCESSED_DIR, source_type)
    os.makedirs(destination_dir, exist_ok=True)

    destination_path = os.path.join(
        destination_dir,
        f"{filename}.json"
    )

    with open(destination_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return destination_path


def process_file(file_path: str, filename: str, source_type: str):

    with logfire.span("Processing File", file=filename):

        try:
            # 1. Save RAW document locally
            raw_path = save_raw_file(file_path, source_type)

            # 2. Extract text
            ext = filename.lower().split(".")[-1]

            if ext == "pdf":
                full_text = parse_pdf(file_path)

            elif ext in ["html", "htm"]:
                full_text = parse_html(file_path)

            elif ext == "txt":
                full_text = parse_text(file_path)

            elif ext in ["docx", "pptx"]:
                from app.ingestion.loaders.office import parse_office
                documents = parse_office(file_path)
                full_text = "\n".join(doc["page_content"] for doc in documents)

            else:
                logfire.warning(
                    f"Unsupported file type: {filename}"
                )
                return

            if not full_text or not full_text.strip():
                logfire.warning(f"No text extracted: {filename}")
                return

            # 3. Chunk text
            chunks = chunk_text(full_text)

            if not chunks:
                return

            # 4. Save processed metadata locally
            processed_data = {
                "filename": filename,
                "chunks": chunks,
                "source_type": source_type
            }

            processed_path = save_processed_data(
                processed_data,
                filename,
                source_type
            )

            # 5. Generate embeddings and index in Qdrant
            with logfire.span("Vectorizing and Indexing"):

                embeddings = embed_texts(chunks)

                points = []

                for i, (chunk, vector) in enumerate(
                    zip(chunks, embeddings)
                ):

                    points.append(
                        models.PointStruct(
                            id=str(uuid.uuid4()),
                            vector=vector,
                            payload={
                                "text": chunk,
                                "source": filename,
                                "source_type": source_type,
                                "chunk_index": i,
                                "raw_path": raw_path,
                                "processed_path": processed_path
                            }
                        )
                    )

                # Upload points to Qdrant in smaller batches
                BATCH_SIZE = 20

                for i in range(0, len(points), BATCH_SIZE):
                    batch = points[i : i + BATCH_SIZE]

                    qdrant.upsert(
                        collection_name=settings.QDRANT_COLLECTION,
                        points=batch,
                        wait=True,
                    )

                    print(
                        f"Uploaded {min(i + BATCH_SIZE, len(points))}/{len(points)} points"
                    )

                logfire.info(f"Indexed {len(points)} chunks for {filename}")

        except Exception as e:
            logfire.error(f"Failed to process {filename}: {e}")
            return


def run_universal_ingestion(
    base_dir: str,
    explicit_source_type: str = None,
    wipe: bool = False
):

    with logfire.span("Universal Ingestion Started"):

        # Create local storage directories
        os.makedirs(RAW_DIR, exist_ok=True)
        os.makedirs(PROCESSED_DIR, exist_ok=True)

        # Wipe Qdrant collection
        if wipe:
            if qdrant.collection_exists(
                settings.QDRANT_COLLECTION
            ):
                qdrant.delete_collection(
                    settings.QDRANT_COLLECTION
                )

                logfire.info("Qdrant collection deleted")

        # Create collection if not exists
        if not qdrant.collection_exists(
            settings.QDRANT_COLLECTION
        ):

            qdrant.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=384,
                    distance=models.Distance.COSINE
                )
            )

        # Scan subdirectories
        subdirs = [
            d for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d))
        ]

        if not subdirs:

            if explicit_source_type:
                source_type = explicit_source_type

            else:
                base_name = os.path.basename(
                    os.path.normpath(base_dir)
                ).lower()

                source_type = (
                    "true" if "true" in base_name
                    else "noisy" if "noisy" in base_name
                    else "general"
                )

            process_directory(base_dir, source_type)

        else:

            for subdir in subdirs:

                source_type = (
                    "true" if "true" in subdir.lower()
                    else "noisy" if "noisy" in subdir.lower()
                    else subdir
                )

                dir_path = os.path.join(base_dir, subdir)

                process_directory(dir_path, source_type)


def process_directory(dir_path: str, source_type: str):

    with logfire.span("Scanning Directory", path=dir_path):

        files = [
            f for f in os.listdir(dir_path)
            if os.path.isfile(os.path.join(dir_path, f))
        ]

        logfire.info(f"Found {len(files)} files")

        for filename in files:

            file_path = os.path.join(dir_path, filename)

            process_file(
                file_path,
                filename,
                source_type
            )


if __name__ == "__main__":

    wipe_requested = "--wipe" in sys.argv

    clean_args = [
        a for a in sys.argv if a != "--wipe"
    ]

    target_dir = (
        clean_args[1] if len(clean_args) > 1 else "DATA"
    )

    explicit_type = (
        clean_args[2] if len(clean_args) > 2 else None
    )

    if not os.path.exists(target_dir):
        print(f"Error: Path {target_dir} does not exist.")
        sys.exit(1)

    run_universal_ingestion(
        target_dir,
        explicit_source_type=explicit_type,
        wipe=wipe_requested
    )

    logfire.info("Ingestion Job Completed")
