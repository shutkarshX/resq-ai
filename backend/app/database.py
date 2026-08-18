"""Database engine and session management.

Uses SQLite for local/demo use. Swapping to Postgres later only requires
changing DATABASE_URL in .env — nothing else in the app needs to change,
since we never rely on SQLite-only features.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resq_ai.db")

# check_same_thread is only needed for SQLite; harmless to gate on it.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Safe to call repeatedly (no-op if tables exist)."""
    # Import models so they're registered on Base.metadata before create_all.
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
