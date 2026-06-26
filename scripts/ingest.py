"""
scripts/ingest.py — Command-line ingestion tool.

Usage:
    python scripts/ingest.py --file knowledge/lecture1.pptx
    python scripts/ingest.py --file knowledge/dav_notes.pdf

Run this from the project root (not from inside scripts/).
This script is the primary way to load DAV course materials during development.
The FastAPI endpoint does the same thing but accepts uploads via HTTP.
"""

import sys
import os
import argparse

# The scripts/ directory is at the project root, one level above backend/.
# We need to add backend/ to sys.path so Python can find our modules
# (database.py, services/, models.py) when this script imports them.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from database import SessionLocal
from services.ingestion import ingest_file


def main():
    parser = argparse.ArgumentParser(
        description="Ingest a course file into the Curra AI knowledge base."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the file to ingest. Supported: .pdf, .pptx, .docx"
    )
    args = parser.parse_args()

    file_path = os.path.abspath(args.file)

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    print(f"⏳ Ingesting: {os.path.basename(file_path)}")

    # Open a DB session, run the pipeline, always close the session.
    db = SessionLocal()
    try:
        result = ingest_file(file_path=file_path, db=db)
        print(f"✅ Done.")
        print(f"   File:   {result['filename']}")
        print(f"   Pages:  {result['pages_parsed']}")
        print(f"   Chunks: {result['chunks_created']}")
        print(f"   Time:   {result['time_seconds']}s")
    except ValueError as e:
        # Unsupported format — user mistake
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ingestion failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()