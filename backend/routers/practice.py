"""
routers/practice.py — Practice Mode endpoints.

Practice Mode presents exam-style questions one at a time and evaluates
student answers against the course materials.

The question bank is built once by calling POST /api/practice/extract.
That endpoint processes the knowledge base in batches, asks GPT-4o to
extract or generate questions from the content, and stores them in the
practice_questions table.

After extraction, the frontend calls GET /api/practice/questions to
populate the question cards. When a student submits an answer,
POST /api/practice/evaluate streams a graded evaluation response.

Endpoints:
    POST /api/practice/extract      Build the question bank from the knowledge base
    GET  /api/practice/questions    List all stored practice questions
    POST /api/practice/evaluate     Evaluate a student's submitted answer (streaming)
"""

import os
import json
from openai import OpenAI
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from database import get_db
from models import PracticeQuestion
from services.retriever import retrieve_chunks
from services.generator import stream_answer

load_dotenv()

router = APIRouter(prefix="/api/practice", tags=["Practice Mode"])
client = OpenAI()

UNIT_NAMESPACE = os.getenv("UNIT_NAMESPACE", "curra_dav_2026_s1")
CHUNK_BATCH    = 5   # Number of chunks per GPT-4o extraction call


@router.post("/extract")
def extract_questions(
    force: bool = False,
    db: Session = Depends(get_db),
):
    """
    Build the practice question bank from the knowledge base.

    Processes chunks in batches of CHUNK_BATCH and asks GPT-4o to
    both find explicit questions in the material and generate
    exam-style questions from the content.

    This is a one-time (or on-demand) operation. It does not run
    automatically on ingestion because it is expensive — it calls
    GPT-4o once per batch of 5 chunks.

    Args:
        force: Re-extract even if questions already exist.
               Without force=true, existing questions are preserved.

    Returns:
        {"questions_created": N, "status": "success"}
    """
    # Avoid duplicate extraction unless forced
    existing = db.query(PracticeQuestion).filter(
        PracticeQuestion.unit_namespace == UNIT_NAMESPACE
    ).count()

    if existing > 0 and not force:
        return {
            "questions_created": 0,
            "existing_questions": existing,
            "status":  "skipped",
            "message": "Questions already extracted. Pass force=true to re-extract."
        }

    # Fetch all chunks with their source document filename
    rows = db.execute(text("""
        SELECT c.content, c.page_number, d.filename
        FROM chunks c
        JOIN documents d ON c.document_id = d.id
        WHERE c.unit_namespace = :namespace
        ORDER BY c.chunk_index
    """), {"namespace": UNIT_NAMESPACE}).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No content in knowledge base.")

    total_created = 0

    for i in range(0, len(rows), CHUNK_BATCH):
        batch = rows[i:i + CHUNK_BATCH]

        batch_context = "\n\n---\n\n".join(
            f"[Page {row.page_number}]\n{row.content}"
            for row in batch
        )

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an exam question creator for a Masters-level "
                        "Data Analytics and Visualisation course. "
                        "From the provided course material, do two things: "
                        "1. Extract any explicit questions or activities you find. "
                        "2. Generate 1-2 exam-style questions based on key concepts. "
                        "For each question provide the expected answer from the material. "
                        "Return ONLY valid JSON: "
                        "{\"questions\": [{\"question_text\": \"string\", "
                        "\"expected_answer\": \"string\", \"topic\": \"string\", "
                        "\"type\": \"extracted|generated\"}]}"
                    )
                },
                {
                    "role": "user",
                    "content": f"Generate practice questions from:\n\n{batch_context}"
                }
            ],
            temperature=0.4,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        questions = data.get("questions", [])

        for q in questions:
            if not q.get("question_text"):
                continue

            # Attribute question to the first chunk in this batch
            db.add(PracticeQuestion(
                question_text=q["question_text"],
                expected_answer=q.get("expected_answer"),
                topic=q.get("topic"),
                source_document=batch[0].filename,
                page_number=batch[0].page_number,
                question_type=q.get("type", "generated"),
                unit_namespace=UNIT_NAMESPACE,
            ))
            total_created += 1

    db.commit()
    return {"questions_created": total_created, "status": "success"}


@router.get("/questions")
def list_questions(db: Session = Depends(get_db)):
    """
    Return all practice questions for this course namespace.

    The frontend renders each question as a card. The expected_answer
    field is intentionally included — the evaluation endpoint compares
    the student's answer against it using GPT-4o, so the frontend
    can optionally hide it until evaluation is complete.

    Returns:
        {
          "questions": [{id, question_text, topic, source_document,
                         page_number, question_type}],
          "total": N
        }
    """
    questions = db.query(PracticeQuestion).filter(
        PracticeQuestion.unit_namespace == UNIT_NAMESPACE
    ).order_by(PracticeQuestion.id).all()

    return {
        "questions": [
            {
                "id":              q.id,
                "question_text":   q.question_text,
                "topic":           q.topic,
                "source_document": q.source_document,
                "page_number":     q.page_number,
                "question_type":   q.question_type,
            }
            for q in questions
        ],
        "total": len(questions)
    }


class EvaluateRequest(BaseModel):
    """
    Request body for evaluating a student's answer.

    question_id:    ID of the PracticeQuestion record in the database.
    student_answer: The student's submitted answer text.
    session_id:     Session identifier (not used here but keeps the
                    API surface consistent with /api/chat).
    """
    question_id:    int
    student_answer: str
    session_id:     str = "practice"


@router.post("/evaluate")
async def evaluate_answer(
    body: EvaluateRequest,
    db: Session = Depends(get_db),
):
    """
    Evaluate a student's answer to a practice question.

    Retrieves the question and its model answer from the database,
    fetches relevant chunks from the knowledge base using the question
    text as the search query, then streams a GPT-4o evaluation.

    The evaluation covers:
    - What the student got right
    - What they missed or got wrong
    - The correct answer sourced from the course materials

    Uses the 'practice' system prompt from generator.py which is
    designed specifically for graded evaluation responses.

    Returns:
        StreamingResponse (SSE) — same format as /api/chat
    """
    question = db.query(PracticeQuestion).filter(
        PracticeQuestion.id == body.question_id
    ).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")

    # Use the question text to find the most relevant knowledge base chunks
    chunks = retrieve_chunks(
        query=question.question_text,
        unit_namespace=UNIT_NAMESPACE,
        db=db,
    )

    # Build a structured evaluation prompt.
    # The model answer (expected_answer) is included so GPT-4o has a
    # reference point — it evaluates the student against the materials,
    # not against its own training knowledge.
    evaluation_query = (
        f"Question: {question.question_text}\n\n"
        f"Model answer from course materials: "
        f"{question.expected_answer or 'Evaluate based on retrieved excerpts only.'}\n\n"
        f"Student's submitted answer:\n{body.student_answer}\n\n"
        "Evaluate this answer."
    )

    async def event_stream():
        # Meta event carries the question for the frontend to display
        yield f"data: {json.dumps({'type': 'meta', 'question': question.question_text, 'topic': question.topic})}\n\n"

        async for token in stream_answer(
            query=evaluation_query,
            chunks=chunks,
            mode="practice",
            history=[],
        ):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )