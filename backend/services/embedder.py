"""
embedder.py — Embedding generation and database storage service.

This is the third and final step in the ingestion pipeline. It takes
the list of chunks produced by the chunker, converts each one into a
1536-dimensional vector using OpenAI's embedding model, and writes
everything to PostgreSQL.

Why text-embedding-3-small?
  It produces 1536-dimensional vectors — the same size as our pgvector
  column. It is the most cost-efficient embedding model from OpenAI
  while still being high quality for semantic similarity tasks.

  Critical: the same model must be used at query time. When a student
  asks a question, we embed the query with text-embedding-3-small and
  compare it against these stored embeddings. If we used a different
  model for the query, the vectors would be in different spaces and
  similarity scores would be meaningless.

Why batch requests?
  Sending 200 chunks as 200 separate API calls would be slow and wasteful.
  The embeddings API accepts up to 2048 texts per call. We use batches
  of 100 — fast and well within limits.

Why flush() before adding chunks?
  SQLAlchemy's flush() sends the INSERT for the Document record to the
  database without committing, which gives us the document.id that each
  Chunk record needs as a foreign key. Without flush(), document.id
  would be None and the Chunk inserts would fail.
"""

import os
import time
from openai import OpenAI
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from models import Document, Chunk as ChunkModel

load_dotenv()

# OpenAI client — reads OPENAI_API_KEY from environment automatically
client = OpenAI()

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


def embed_and_store(
    file_path: str,
    chunks: list[dict],
    unit_namespace: str,
    db: Session,
) -> int:
    """
    Embed all chunks and write them to the database.

    Args:
        file_path:      Path to the source file — used to extract the filename
        chunks:         Output from chunker.chunk_pages()
        unit_namespace: Course identifier scoping these chunks (e.g. "curra_dav_2026_s1")
        db:             SQLAlchemy session

    Returns:
        Total number of chunks successfully stored.
    """
    filename = os.path.basename(file_path)

    # Create the Document record. chunk_count is 0 for now — updated at the end.
    document = Document(
        filename=filename,
        unit_namespace=unit_namespace,
        chunk_count=0,
    )
    db.add(document)

    # flush() sends the INSERT to PostgreSQL and populates document.id
    # without committing the transaction. We need document.id so the
    # Chunk records can reference it via the foreign key.
    db.flush()

    total_stored = 0

    for batch_start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[batch_start:batch_start + BATCH_SIZE]
        batch_texts = [chunk["content"] for chunk in batch]

        # Send batch to OpenAI — returns one embedding vector per input text
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch_texts,
        )

        # zip() pairs each chunk dict with its corresponding embedding result
        for chunk_data, embedding_obj in zip(batch, response.data):
            db_chunk = ChunkModel(
                document_id=document.id,
                content=chunk_data["content"],
                embedding=embedding_obj.embedding,  # list of 1536 floats
                chunk_index=chunk_data["chunk_index"],
                page_number=chunk_data["page_number"],
                unit_namespace=unit_namespace,
            )
            db.add(db_chunk)
            total_stored += 1

        # Brief pause between batches — courteous to the API rate limits
        if batch_start + BATCH_SIZE < len(chunks):
            time.sleep(0.5)

    # Update the document record with the final chunk count
    document.chunk_count = total_stored

    # Commit the whole transaction atomically.
    # Document + all Chunks are written together. If anything above raised
    # an exception, nothing is committed — the DB stays clean.
    db.commit()

    return total_stored