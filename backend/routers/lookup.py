"""
routers/lookup.py — Quick Lookup endpoint.

Quick Lookup is the fastest study mode. The student types a term
and immediately gets a concise definition sourced from their slides.

Design decisions:
  - Non-streaming: returns JSON directly, not an SSE stream.
    A 2-4 sentence definition does not benefit from streaming —
    the full response arrives before the first token would even
    render in a stream.
  - top_k=1: only the single best-matching chunk is used.
    Lookup is about precision, not breadth. If the best chunk
    is not a strong match (score < 0.5), we return Not Found
    rather than guessing.
  - max_tokens=200: enforces the concise output requirement.
    Without this cap, GPT-4o tends to elaborate beyond 4 sentences.

Endpoint:
    GET /api/lookup?term=k-means+clustering
"""

import os
from openai import OpenAI
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db
from services.retriever import retrieve_chunks

load_dotenv()

router = APIRouter(prefix="/api", tags=["Quick Lookup"])
client = OpenAI()

UNIT_NAMESPACE      = os.getenv("UNIT_NAMESPACE", "curra_dav_2026_s1")
LOOKUP_MIN_SCORE    = 0.5   # Below this, we return Not Found rather than guessing
LOOKUP_MAX_TOKENS   = 200   # Enforces the 2-4 sentence constraint


@router.get("/lookup")
def quick_lookup(
    term: str,
    db: Session = Depends(get_db),
):
    """
    Return a concise definition of a term from the course materials.

    If the best matching chunk scores below LOOKUP_MIN_SCORE, the term
    is considered not covered in the uploaded materials and a Not Found
    response is returned. This is the correct behaviour — a weak match
    should not produce a hallucinated definition.

    Args:
        term: The term or concept to look up (URL query parameter)

    Returns:
        {
          "term": "k-means clustering",
          "definition": "K-means is... (Intro to Data Analytics, Page 12)",
          "found": true,
          "source": {"filename": "...", "page_number": 12, "score": 0.81}
        }

        or if not found:
        {
          "term": "Black-Scholes",
          "definition": null,
          "found": false,
          "message": "This term is not covered in the uploaded course materials."
        }
    """
    # Retrieve only the single best-matching chunk
    chunks = retrieve_chunks(
        query=term,
        unit_namespace=UNIT_NAMESPACE,
        db=db,
        top_k=1,
    )

    # No chunks or weak match → Not Found
    if not chunks or chunks[0]["score"] < LOOKUP_MIN_SCORE:
        return {
            "term":       term,
            "definition": None,
            "found":      False,
            "message":    "This term is not well covered in the uploaded course materials.",
        }

    top = chunks[0]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a quick reference tool for a Data Analytics and Visualisation course. "
                    "Give a precise 2-4 sentence definition of the requested term using ONLY "
                    "the provided course material excerpt. "
                    "End your response with the citation in brackets: (Filename, Page N). "
                    "Do not elaborate beyond the definition. Be accurate and concise."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Define: {term}\n\n"
                    f"Course material excerpt:\n"
                    f"[{top['filename']}, Page {top['page_number']}]\n"
                    f"{top['content']}"
                )
            }
        ],
        temperature=0.1,
        max_tokens=LOOKUP_MAX_TOKENS,
    )

    return {
        "term":       term,
        "definition": response.choices[0].message.content,
        "found":      True,
        "source": {
            "filename":    top["filename"],
            "page_number": top["page_number"],
            "score":       round(top["score"], 3),
        },
    }