import os
import redis as redis_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import Base, engine, check_db_connection
import models  # noqa: F401

# Import the ingestion router — registers POST /api/ingest
from routers.ingest import router as ingest_router
from routers.chat import router as chat_router
from routers.revision import router as revision_router
from routers.practice import router as practice_router
from routers.lookup   import router as lookup_router
from routers.demo import router as demo_router

load_dotenv()

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

# Register all routers with the app.
# Any route defined in routers/ingest.py is now accessible on this server.
app.include_router(ingest_router)
app.include_router(chat_router)
app.include_router(revision_router)
app.include_router(practice_router)
app.include_router(lookup_router)
app.include_router(demo_router)

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created / verified")


def check_redis_connection() -> bool:
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis_client.from_url(redis_url)
        r.ping()
        return True
    except Exception:
        return False


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "curra-ai-backend", "version": "1.0.0"}


@app.get("/health/db", tags=["Health"])
async def health_db():
    ok = check_db_connection()
    return {"status": "ok" if ok else "error", "database": "connected" if ok else "unreachable"}


@app.get("/health/redis", tags=["Health"])
async def health_redis():
    ok = check_redis_connection()
    return {"status": "ok" if ok else "error", "redis": "connected" if ok else "unreachable"}


@app.get("/health/all", tags=["Health"])
async def health_all():
    db_ok    = check_db_connection()
    redis_ok = check_redis_connection()
    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "checks": {"api": True, "database": db_ok, "redis": redis_ok}
    }