"""
routers/chat.py — Chat endpoint for all five study modes.

POST /api/chat
    Accepts a student message and returns a Server-Sent Events stream.

Request body:
    {
        "message":    "What is k-means clustering?",
        "session_id": "abc123",
        "mode":       "free"
    }

SSE response format (one event per line-pair):
    data: {"type": "meta", "confidence": "High", "sources": [...]}
    data: {"type": "token", "content": "K-means"}
    data: {"type": "token", "content": " clustering"}
    ...
    data: {"type": "done"}

The meta event arrives first so the frontend can show the confidence
badge and source citations before the answer starts streaming in.

Session history:
    Stored in Redis. Each session keeps the last 10 messages (5 exchanges).
    Sessions expire after 24 hours of inactivity.
    Redis key: curra:session:{session_id}
"""

import os
import json
import redis as redis_client
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db
from models import Gap
from services.retriever import retrieve_chunks, get_confidence_label
from services.generator import stream_answer

load_dotenv()

router = APIRouter(prefix="/api", tags=["Chat"])

UNIT_NAMESPACE = os.getenv("UNIT_NAMESPACE", "curra_dav_2026_s1")
REDIS_URL      = os.getenv("REDIS_URL", "redis://localhost:6379")
MAX_HISTORY    = 10     # Max messages stored per session (5 user + 5 assistant)
SESSION_TTL    = 86400  # Session expiry: 24 hours in seconds


class ChatRequest(BaseModel):
    """
    Pydantic model for the chat request body.

    Pydantic validates incoming JSON automatically. FastAPI returns a
    422 error if any required field is missing or the wrong type —
    no manual validation needed.

    message:    The student's question for this turn.
    session_id: Unique ID for this study session. The frontend generates
                a UUID when the student starts a session and sends the
                same ID on every message so history is preserved.
    mode:       Active study mode. Defaults to "free" if omitted.
    """
    message: str
    session_id: str
    mode: str = "free"


def get_redis():
    """Return a Redis connection from the configured URL."""
    return redis_client.from_url(REDIS_URL, decode_responses=True)


def load_history(session_id: str) -> list[dict]:
    """
    Load conversation history for this session from Redis.

    Returns empty list for new sessions or expired sessions.
    Format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    r = get_redis()
    raw = r.get(f"curra:session:{session_id}")
    if not raw:
        return []
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def save_history(session_id: str, history: list[dict]) -> None:
    """
    Persist updated conversation history to Redis.

    Trims to MAX_HISTORY before saving — older messages are dropped.
    Resets the TTL so active sessions stay alive.
    """
    r = get_redis()
    trimmed = history[-MAX_HISTORY:]
    r.set(f"curra:session:{session_id}", json.dumps(trimmed), ex=SESSION_TTL)


def log_gap(query: str, confidence_score: float, db: Session) -> None:
    """
    Write a low-confidence query to the gaps table.

    Called when the best similarity score is below 0.5 — meaning the
    knowledge base has poor coverage of this topic.

    Gap records power the lecturer demo dashboard: the DAV lecturer
    can see exactly which questions their uploaded materials cannot answer.
    """
    gap = Gap(
        query=query,
        unit_namespace=UNIT_NAMESPACE,
        confidence=confidence_score,
    )
    db.add(gap)
    db.commit()


@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Main study assistant endpoint.

    Pipeline:
        1. Load conversation history from Redis
        2. Retrieve top 5 relevant chunks from pgvector
        3. Determine confidence label from similarity scores
        4. Log to gaps table if confidence is Low
        5. Stream GPT-4o answer as Server-Sent Events
        6. Save the new exchange to Redis after streaming completes

    Returns:
        StreamingResponse (text/event-stream) — the SSE stream.
    """
    # Validate mode — silently fall back to free for unrecognised values
    valid_modes = {"free", "revision", "deepdive", "practice", "lookup"}
    mode = request.mode if request.mode in valid_modes else "free"

    # Step 1 — Load history
    history = load_history(request.session_id)

    # Step 2 — Retrieve relevant chunks from pgvector
    chunks = retrieve_chunks(
        query=request.message,
        unit_namespace=UNIT_NAMESPACE,
        db=db,
    )

    # Step 3 — Confidence label
    confidence_label = get_confidence_label(chunks)
    top_score = chunks[0]["score"] if chunks else 0.0

    # Step 4 — Log gap if Low confidence
    if confidence_label == "Low":
        log_gap(query=request.message, confidence_score=top_score, db=db)

    # Build source list for the meta event
    sources = [
        {
            "filename":    c["filename"],
            "page_number": c["page_number"],
            "score":       round(c["score"], 3),
        }
        for c in chunks
    ]

    async def event_stream():
        """
        Async generator producing the SSE response body.

        SSE wire format: each event is "data: <payload>\\n\\n"
        The double newline is the event delimiter — the browser's
        EventSource API uses it to know one event has ended.

        Event sequence:
            1. meta  — confidence + sources (sent before first token)
            2. token — one per GPT-4o output token
            3. done  — signals the client to close the stream
        """
        full_answer = ""

        # Meta event first — client can render citations while answer streams
        yield f"data: {json.dumps({'type': 'meta', 'confidence': confidence_label, 'sources': sources})}\n\n"

        # Stream tokens from GPT-4o
        async for token in stream_answer(
            query=request.message,
            chunks=chunks,
            mode=mode,
            history=history,
        ):
            full_answer += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        # Done event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

        # Step 6 — Persist this exchange to Redis
        # Done here (after streaming) so we have the complete answer text.
        updated_history = history + [
            {"role": "user",      "content": request.message},
            {"role": "assistant", "content": full_answer},
        ]
        save_history(request.session_id, updated_history)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            # Prevent proxies and browsers from buffering SSE events.
            # Without these, some environments batch events and the
            # streaming effect is completely lost.
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",
        },
    )