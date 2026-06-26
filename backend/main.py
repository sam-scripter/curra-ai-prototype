import os
import redis as redis_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import Base, engine, check_db_connection
import models  # noqa: F401

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


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created / verified")


def check_redis_connection() -> bool:
    """Pings Redis to confirm it is reachable."""
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6380")
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
    return {
        "status": "ok" if ok else "error",
        "database": "connected" if ok else "unreachable"
    }


@app.get("/health/redis", tags=["Health"])
async def health_redis():
    """Confirms Redis is reachable. Redis will cache repeated queries
    in Phase 3 and store session history in Phase 4."""
    ok = check_redis_connection()
    return {
        "status": "ok" if ok else "error",
        "redis": "connected" if ok else "unreachable"
    }


@app.get("/health/all", tags=["Health"])
async def health_all():
    """Single call to check all three services at once.
    Useful before running a demo to confirm everything is up."""
    db_ok    = check_db_connection()
    redis_ok = check_redis_connection()
    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "checks": {
            "api":      True,
            "database": db_ok,
            "redis":    redis_ok,
        }
    }