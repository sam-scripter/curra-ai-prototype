import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

# Load variables from .env into os.environ
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Fallback for running backend directly on your machine (outside Docker)
    "postgresql://curra_user:curra_pass@localhost:5433/curra_db"
)

# The engine is the core SQLAlchemy connection pool.
# It manages a set of real database connections and hands them out as needed.
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory. Every time you call SessionLocal() you get
# a fresh database session — an isolated unit of work with its own
# transaction. Sessions are never shared between requests.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base is the parent class all our models inherit from.
# SQLAlchemy uses it to track which Python classes map to which tables.
class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency. Yields a database session per request
    and guarantees it is closed when the request finishes,
    even if an exception is raised.
    
    Usage in a route:
        from database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends
        
        @app.get("/something")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Runs a trivial query to verify the database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False