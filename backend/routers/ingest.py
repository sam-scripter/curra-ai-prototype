"""
routers/ingest.py — File upload and ingestion endpoint.

POST /api/ingest
    Accepts a multipart file upload, saves it to the knowledge/ directory,
    and runs the ingestion pipeline on it.

During development the CLI script is more convenient. This endpoint
becomes useful in Phase 6 when the lecturer demo dashboard uploads
files through the browser UI.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from services.ingestion import ingest_file

router = APIRouter(prefix="/api", tags=["Ingestion"])

# knowledge/ sits at the project root, two levels above this file.
# __file__ is backend/routers/ingest.py → ../../knowledge
KNOWLEDGE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "knowledge")
)


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a course material file and ingest it into the knowledge base.

    The file is saved to knowledge/ first, then parsed, chunked,
    embedded, and stored in PostgreSQL.

    Args:
        file: Multipart file upload — PDF, PPTX, or DOCX
        db:   Injected database session

    Returns:
        {filename, pages_parsed, chunks_created, time_seconds, status}
    """
    filename = file.filename or ""
    extension = os.path.splitext(filename)[1].lower()

    if extension not in [".pdf", ".pptx", ".docx"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Accepted: .pdf, .pptx, .docx"
        )

    # Save the uploaded file to disk
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    save_path = os.path.join(KNOWLEDGE_DIR, filename)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run the pipeline on the saved file
    try:
        result = ingest_file(file_path=save_path, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    return result