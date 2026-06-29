"""
routers/demo.py — Lecturer demo dashboard endpoints.

Three read-only endpoints that power the /demo frontend page:

    GET /api/demo/stats       — aggregate numbers (documents, chunks, queries, gaps)
    GET /api/demo/documents   — list of ingested files with chunk counts
    GET /api/demo/gaps        — full gap log ordered by most recent

These endpoints are intentionally read-only. No authentication is
applied in the prototype — the dashboard URL is the only access control.
The full system would gate this behind a lecturer login.
"""

import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from dotenv import load_dotenv

from database import get_db
from models import Document, Gap, QueryLog

load_dotenv()

router = APIRouter(prefix="/api/demo", tags=["Demo Dashboard"])

UNIT_NAMESPACE = os.getenv("UNIT_NAMESPACE", "curra_dav_2026_s1")


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """
    Return aggregate statistics for the demo dashboard header cards.

    Computes:
      - documents: number of files ingested
      - total_chunks: sum of all text chunks across all documents
      - total_queries: total questions asked via /api/chat
      - gaps_logged: questions with Low confidence (not covered in materials)
      - confidence_breakdown: count per confidence level for the pie/bar chart

    All figures are scoped to UNIT_NAMESPACE so if the full system
    ever runs multiple courses, each gets its own stats.
    """
    # Document and chunk counts
    doc_count = db.query(Document).filter(
        Document.unit_namespace == UNIT_NAMESPACE
    ).count()

    chunk_count = db.execute(text("""
        SELECT COALESCE(SUM(chunk_count), 0)
        FROM documents
        WHERE unit_namespace = :namespace
    """), {"namespace": UNIT_NAMESPACE}).scalar()

    # Query stats from query_logs
    total_queries = db.query(QueryLog).filter(
        QueryLog.unit_namespace == UNIT_NAMESPACE
    ).count()

    # Confidence breakdown — count per level
    breakdown_rows = db.execute(text("""
        SELECT confidence, COUNT(*) as count
        FROM query_logs
        WHERE unit_namespace = :namespace
        GROUP BY confidence
    """), {"namespace": UNIT_NAMESPACE}).fetchall()

    confidence_breakdown = {"High": 0, "Medium": 0, "Low": 0}
    for row in breakdown_rows:
        if row.confidence in confidence_breakdown:
            confidence_breakdown[row.confidence] = row.count

    # Gap count from gaps table
    gaps_logged = db.query(Gap).filter(
        Gap.unit_namespace == UNIT_NAMESPACE
    ).count()

    return {
        "documents":            doc_count,
        "total_chunks":         int(chunk_count or 0),
        "total_queries":        total_queries,
        "gaps_logged":          gaps_logged,
        "confidence_breakdown": confidence_breakdown,
    }


@router.get("/documents")
def get_documents(db: Session = Depends(get_db)):
    """
    Return all ingested documents with their chunk counts.

    Shown on the dashboard as a table so the lecturer can see exactly
    which of their files are powering the AI responses.
    Ordered by upload date ascending so the first ingested file appears first.
    """
    documents = db.query(Document).filter(
        Document.unit_namespace == UNIT_NAMESPACE
    ).order_by(Document.uploaded_at.asc()).all()

    return {
        "documents": [
            {
                "id":          doc.id,
                "filename":    doc.filename,
                "chunk_count": doc.chunk_count,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            }
            for doc in documents
        ],
        "total": len(documents),
    }


@router.get("/gaps")
def get_gaps(db: Session = Depends(get_db)):
    """
    Return all logged knowledge gaps ordered by most recent first.

    This is the most important section of the lecturer demo.
    Each gap is a real question a student asked that the uploaded
    materials couldn't answer — direct evidence of curriculum gaps.

    The confidence score is included so the lecturer can see how
    poorly matched the query was (lower = bigger gap).
    """
    gaps = db.query(Gap).filter(
        Gap.unit_namespace == UNIT_NAMESPACE
    ).order_by(Gap.asked_at.desc()).all()

    return {
        "gaps": [
            {
                "id":         gap.id,
                "query":      gap.query,
                "confidence": round(gap.confidence, 3),
                "asked_at":   gap.asked_at.isoformat() if gap.asked_at else None,
            }
            for gap in gaps
        ],
        "total": len(gaps),
    }