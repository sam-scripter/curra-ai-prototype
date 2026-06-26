"""
retriever.py — Semantic similarity search service.

First step in the query pipeline. Given a student's question,
it finds the most semantically similar chunks in the knowledge base.

The process:
  1. Embed the query using text-embedding-3-small — the same model
     used at ingestion time. This is non-negotiable: vectors only
     have meaning relative to the model that produced them. Using a
     different model at query time would be like searching an English
     dictionary with a French query — the space is incompatible.

  2. Run cosine similarity search via pgvector's <=> operator.
     pgvector compares the query vector against every stored chunk
     vector and returns the closest ones in milliseconds.

  3. Attach a confidence label to the result based on how strong
     the best match is. This label travels with the response all
     the way to the student's screen.
"""

import os
from typing import TypedDict
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

# Sync client is fine here — retrieval is called once per request
# and we await the entire route anyway at the StreamingResponse level.
client = OpenAI()

EMBEDDING_MODEL = "text-embedding-3-small"


class RetrievedChunk(TypedDict):
    """
    One chunk returned from similarity search, enriched with source metadata.

    id:          Database row ID
    content:     The raw text — what gets injected into the GPT-4o prompt
    filename:    Source document — shown to the student as a citation
    page_number: Source page/slide — shown alongside the filename
    chunk_index: Position in the document — useful for debugging ordering
    score:       Cosine similarity score (0.0–1.0)
                 > 0.75 → High confidence
                 0.50–0.75 → Medium confidence
                 < 0.50 → Low confidence (gap logged)
    """
    id: int
    content: str
    filename: str
    page_number: int
    chunk_index: int
    score: float


def embed_query(query: str) -> list[float]:
    """
    Convert the student's question into a 1536-dimensional vector.

    Identical to what happens during ingestion. The resulting vector
    lives in the same mathematical space as the stored chunk embeddings,
    which is what makes comparison meaningful.
    """
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    return response.data[0].embedding


def retrieve_chunks(
    query: str,
    unit_namespace: str,
    db: Session,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """
    Find the top_k most semantically similar chunks for a given query.

    Uses pgvector's <=> cosine distance operator to rank all chunks
    in the namespace by similarity to the query vector.

    The JOIN with documents gives us the filename for citations
    without a second round trip to the database.

    Args:
        query:          Student's question in plain text
        unit_namespace: Course identifier — only searches this course's chunks.
                        Prevents DAV answers bleeding into other courses
                        in the full multi-course system.
        db:             SQLAlchemy session
        top_k:          Number of chunks to return (default 5)

    Returns:
        List of RetrievedChunk dicts ordered by similarity score descending.
        Empty list if the knowledge base has no chunks.
    """
    # Embed the query into a vector
    query_vector = embed_query(query)

    # pgvector expects the vector as a string: "[0.12, -0.34, ...]"
    embedding_str = "[" + ",".join(map(str, query_vector)) + "]"

    # Cosine distance search.
    # <=> is pgvector's cosine distance operator (distance = 1 - similarity).
    # ORDER BY distance ASC = ORDER BY similarity DESC (most similar first).
    # 1 - (embedding <=> query) converts distance back to similarity score.
    sql = text("""
        SELECT
            c.id,
            c.content,
            c.page_number,
            c.chunk_index,
            d.filename,
            1 - (c.embedding <=> CAST(:embedding AS vector)) AS score
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.unit_namespace = :namespace
        ORDER BY c.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    rows = db.execute(sql, {
        "embedding": embedding_str,
        "namespace": unit_namespace,
        "top_k":     top_k,
    }).fetchall()

    return [
        {
            "id":          row.id,
            "content":     row.content,
            "filename":    row.filename,
            "page_number": row.page_number,
            "chunk_index": row.chunk_index,
            "score":       float(row.score),
        }
        for row in rows
    ]


def get_confidence_label(chunks: list[RetrievedChunk]) -> str:
    """
    Derive a confidence label from the top chunk's similarity score.

    Only the top score matters — if the best match is weak, additional
    chunks will not rescue the answer.

    Thresholds:
        High   (≥ 0.75): Strong match. Answer is reliable.
        Medium (≥ 0.50): Partial match. Answer is reasonable but may be incomplete.
        Low    (< 0.50): Poor match. Topic likely not covered in uploaded materials.
    """
    if not chunks:
        return "Low"

    top_score = chunks[0]["score"]

    if top_score >= 0.75:
        return "High"
    elif top_score >= 0.50:
        return "Medium"
    else:
        return "Low"