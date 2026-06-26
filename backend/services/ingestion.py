"""
ingestion.py — Pipeline orchestrator.

Connects parser → chunker → embedder into a single ingest_file() function.

Both the CLI script (scripts/ingest.py) and the FastAPI endpoint
(routers/ingest.py) call this function. Keeping the pipeline logic here
means changes only need to be made in one place.
"""

import os
import time
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from services.parser import parse_file
from services.chunker import chunk_pages
from services.embedder import embed_and_store

load_dotenv()


def ingest_file(file_path: str, db: Session) -> dict:
    """
    Run the full ingestion pipeline for one file.

    Steps:
        1. parse_file()      → extract text from PDF/PPTX/DOCX
        2. chunk_pages()     → split into 500-token segments with 50-token overlap
        3. embed_and_store() → embed each chunk and write to PostgreSQL

    Args:
        file_path: Absolute path to the file to ingest
        db:        SQLAlchemy session

    Returns:
        Stats dict: {filename, pages_parsed, chunks_created, time_seconds, status}
    """
    start_time = time.time()
    unit_namespace = os.getenv("UNIT_NAMESPACE", "curra_dav_2026_s1")

    # Step 1 — Parse
    pages = parse_file(file_path)

    # Step 2 — Chunk
    chunks = chunk_pages(pages)

    # Step 3 — Embed and store
    chunks_stored = embed_and_store(
        file_path=file_path,
        chunks=chunks,
        unit_namespace=unit_namespace,
        db=db,
    )

    elapsed = round(time.time() - start_time, 2)

    return {
        "filename":       os.path.basename(file_path),
        "pages_parsed":   len(pages),
        "chunks_created": chunks_stored,
        "time_seconds":   elapsed,
        "status":         "success",
    }