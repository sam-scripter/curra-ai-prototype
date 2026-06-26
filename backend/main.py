from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPI creates the ASGI application.
# title and version appear in the auto-generated docs at /docs
app = FastAPI(
    title="Curra AI",
    description="Curriculum-grounded AI study assistant — DAV prototype",
    version="1.0.0",
)

# CORS middleware lets the Next.js frontend (port 3000) make requests
# to this backend (port 8000) without being blocked by the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health():
    """Basic liveness check. Returns 200 if the server is running."""
    return {"status": "ok", "service": "curra-ai-backend", "version": "1.0.0"}