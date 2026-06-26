"""
routers/revision.py — Revision Mode structured setup endpoints.

Revision Mode has a two-step setup flow before the study session begins:
  1. Student sees the list of topics covered in their uploaded materials
  2. Student provides exam date + confidence → receives a prioritised plan

After setup, the revision session itself uses the existing /api/chat
endpoint with mode='revision'. The system prompt there handles the
interactive explain → test → feedback loop.

These endpoints return structured JSON (not streams) because the frontend
renders them as UI elements: a checklist of topics, a study schedule.

Endpoints:
    GET  /api/revision/topics   Detect and return all topic areas in the knowledge base
    POST /api/revision/plan     Generate a prioritised revision plan from topics + student input
"""

import os
import json
import redis as redis_client
from openai import OpenAI
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from database import get_db

load_dotenv()

router = APIRouter(prefix="/api/revision", tags=["Revision Mode"])

# Sync OpenAI client — these endpoints return JSON, not streams
client = OpenAI()

UNIT_NAMESPACE   = os.getenv("UNIT_NAMESPACE", "curra_dav_2026_s1")
REDIS_URL        = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis key for caching detected topics.
# Topics only change when new files are ingested, so a 1-hour TTL
# avoids repeated GPT-4o calls for every student who opens Revision Mode.
TOPICS_CACHE_KEY = f"curra:topics:{UNIT_NAMESPACE}"
TOPICS_CACHE_TTL = 3600  # seconds


def get_redis():
    return redis_client.from_url(REDIS_URL, decode_responses=True)


def _detect_topics(db: Session) -> list[str]:
    """
    Internal helper: fetch a chunk sample and ask GPT-4o to extract topic labels.

    Samples the first chunk from each page (up to 20 pages) to get a
    representative cross-section of the document without sending the
    entire knowledge base to GPT-4o.

    Returns a list of topic name strings.
    """
    rows = db.execute(text("""
        SELECT DISTINCT ON (page_number) content, page_number
        FROM chunks
        WHERE unit_namespace = :namespace
        ORDER BY page_number, chunk_index
        LIMIT 20
    """), {"namespace": UNIT_NAMESPACE}).fetchall()

    if not rows:
        return []

    sample_text = "\n\n---\n\n".join(
        f"[Page {row.page_number}]\n{row.content[:400]}"
        for row in rows
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a curriculum analyst for a Masters-level Data Analytics "
                    "and Visualisation course. Identify the distinct topic areas covered "
                    "in these course material excerpts. "
                    "Return ONLY valid JSON in this exact format: "
                    "{\"topics\": [\"Topic Name 1\", \"Topic Name 2\", ...]}"
                    "Be specific but concise. Maximum 15 topics."
                )
            },
            {
                "role": "user",
                "content": f"Identify the distinct topic areas:\n\n{sample_text}"
            }
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    parsed = json.loads(response.choices[0].message.content)
    return parsed.get("topics", [])


@router.get("/topics")
def get_topics(db: Session = Depends(get_db)):
    """
    Return all topic areas detected in the knowledge base.

    Checks Redis cache first. On cache miss, asks GPT-4o to analyse
    a sample of chunks and extract distinct topic labels, then caches
    the result for 1 hour.

    The frontend renders this as a checklist during the Revision Mode
    setup flow so the student can mark which topics they already know.

    Returns:
        {
          "topics": ["Introduction to Data Analytics", "Types of Analytics", ...],
          "source": "cache" | "generated"
        }
    """
    r = get_redis()

    # Return cached topics if available
    cached = r.get(TOPICS_CACHE_KEY)
    if cached:
        return {"topics": json.loads(cached), "source": "cache"}

    topics = _detect_topics(db)

    if not topics:
        raise HTTPException(
            status_code=404,
            detail="No content in knowledge base. Upload course materials first."
        )

    # Cache the result
    r.set(TOPICS_CACHE_KEY, json.dumps(topics), ex=TOPICS_CACHE_TTL)

    return {"topics": topics, "source": "generated"}


class RevisionPlanRequest(BaseModel):
    """
    Request body for generating a personalised revision plan.

    exam_date:     When the exam or CAT is (free text — e.g. "July 15, 2026"
                   or "in 2 weeks"). GPT-4o interprets this contextually.
    confidence:    Student's overall self-assessed confidence: "low", "medium", "high"
    strong_topics: Topics the student already feels confident about.
                   These are deprioritised (quick review only), not removed.
    """
    exam_date:     str
    confidence:    str = "medium"
    strong_topics: list[str] = []


@router.post("/plan")
def generate_revision_plan(
    body: RevisionPlanRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a personalised, prioritised revision plan.

    Fetches the topic list (from cache or generating it fresh), then
    asks GPT-4o to order them by complexity and exam relevance given
    the student's timeline and confidence.

    Returns structured JSON — not a stream — because the frontend
    renders this as a visual study schedule, not a chat message.

    Returns:
        {
          "plan": [
            {
              "topic": "K-Means Clustering",
              "priority": "High",
              "estimated_minutes": 45,
              "reason": "Core algorithm, likely exam-heavy, marked as weak"
            },
            ...
          ],
          "total_minutes": 285,
          "exam_date": "July 15, 2026"
        }
    """
    # Get topics from cache or generate fresh
    r = get_redis()
    cached = r.get(TOPICS_CACHE_KEY)

    if cached:
        topics = json.loads(cached)
    else:
        topics = _detect_topics(db)
        if topics:
            r.set(TOPICS_CACHE_KEY, json.dumps(topics), ex=TOPICS_CACHE_TTL)

    if not topics:
        raise HTTPException(
            status_code=404,
            detail="No topics found. Upload course materials first."
        )

    # Annotate each topic so GPT-4o knows which to deprioritise
    topics_context = "\n".join(
        f"- {t}{'  [ALREADY STRONG — quick review only]' if t in body.strong_topics else ''}"
        for t in topics
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a study planner for a Masters-level Data Analytics and "
                    "Visualisation course. Create a prioritised revision plan. "
                    "Return ONLY valid JSON in this exact format: "
                    "{\"plan\": [{\"topic\": \"string\", \"priority\": \"High|Medium|Low\", "
                    "\"estimated_minutes\": number, \"reason\": \"string\"}], "
                    "\"total_minutes\": number}"
                    "High priority: 45-60 min. Medium: 30-45 min. Low: 15-30 min. "
                    "Strong topics (quick review): 15 min. Order by priority descending."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Exam date: {body.exam_date}\n"
                    f"Student confidence: {body.confidence}\n"
                    f"Topics:\n{topics_context}\n\n"
                    "Generate the revision plan."
                )
            }
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    plan_data = json.loads(response.choices[0].message.content)
    plan_data["exam_date"] = body.exam_date

    return plan_data