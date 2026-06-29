"""
classifier.py — Class activity detection service.

At query time, before generating any answer, the chat endpoint calls
detect_class_activity() to check whether the student's question
matches a stored class activity question.

If it does, the chat endpoint switches to Socratic mode — guiding
the student toward the answer rather than providing it directly.

Why 0.85 threshold?
  Standard similarity search uses 0.75 for High confidence answers.
  For class activity detection we use a higher bar — 0.85 — because
  the cost of a false positive (refusing to answer a legitimate study
  question) is higher than the cost of a false negative (answering
  something that was an activity).

  0.85 means the question must be very close to the stored activity —
  paraphrasing the same exercise, not just asking about the same topic.
"""

import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

UNIT_NAMESPACE           = os.getenv("UNIT_NAMESPACE", "curra_dav_2026_s1")
CLASS_ACTIVITY_THRESHOLD = 0.85


def detect_class_activity(
    query_embedding: list[float],
    db: Session,
) -> tuple[bool, float, str | None]:
    """
    Check whether a student's query matches a stored class activity question.

    Compares the query embedding against all stored class activity question
    embeddings using cosine similarity. Returns the result of the best match.

    Args:
        query_embedding: The 1536-dim embedding of the student's query.
        db:              SQLAlchemy session.

    Returns:
        Tuple of (is_class_activity, best_score, matched_question_text)
        - is_class_activity: True if score exceeds threshold
        - best_score:        The highest similarity score found (0.0 if none)
        - matched_question:  The text of the matched question (None if no match)
    """
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    result = db.execute(text("""
        SELECT
            question_text,
            1 - (question_embedding <=> CAST(:embedding AS vector)) AS score
        FROM practice_questions
        WHERE unit_namespace = :namespace
          AND question_type   = 'class_activity'
          AND question_embedding IS NOT NULL
        ORDER BY question_embedding <=> CAST(:embedding AS vector)
        LIMIT 1
    """), {
        "embedding": embedding_str,
        "namespace": UNIT_NAMESPACE,
    }).fetchone()

    if not result:
        return False, 0.0, None

    score = float(result.score)
    is_activity = score >= CLASS_ACTIVITY_THRESHOLD

    return is_activity, score, result.question_text if is_activity else None

def detect_question_type(query: str) -> str:
    """
    Quickly classify a query to determine handling mode.
    
    Returns:
        'code'   — programming exercise, use code_guide prompt
        'video'  — references an external video, use socratic_video prompt  
        'normal' — proceed with standard class activity or normal flow
    """
    query_lower = query.lower()
    
    # Programming exercise signals
    code_signals = [
        "write a program", "write a python", "python program",
        "write code", "print your name", "displays", "prompts a user",
        "calculates", "asks the user", "program that"
    ]
    if any(signal in query_lower for signal in code_signals):
        return "code"
    
    # Video-dependent activity signals
    video_signals = [
        "as captured in", "from the video", "in this video",
        "captured in the video", "from this video", "watch"
    ]
    if any(signal in query_lower for signal in video_signals):
        return "video"
    
    return "normal"