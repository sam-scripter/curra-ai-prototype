from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, check_db_connection
import models  # noqa: F401 — importing models registers them with Base so create_all sees them

app = FastAPI(
    title="Curra AI",
    description="Curriculum-grounded AI study assistant — DAV prototype",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """
    Runs once when the FastAPI server starts.
    create_all checks whether each table already exists before creating it,
    so it is safe to run on every startup — it never overwrites existing data.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created / verified")


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "curra-ai-backend", "version": "1.0.0"}


@app.get("/health/db", tags=["Health"])
async def health_db():
    """Confirms PostgreSQL is reachable and the connection pool is working."""
    ok = check_db_connection()
    return {
        "status": "ok" if ok else "error",
        "database": "connected" if ok else "unreachable"
    }