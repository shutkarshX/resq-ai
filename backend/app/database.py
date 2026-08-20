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
    # Lightweight compatibility migration for existing local V2 SQLite demos.
    # New installations get the column from SQLAlchemy metadata above.
    if DATABASE_URL.startswith("sqlite"):
        with engine.begin() as connection:
            columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(dispatch_actions)")}
            if "report_id" not in columns:
                connection.exec_driver_sql("ALTER TABLE dispatch_actions ADD COLUMN report_id VARCHAR")
            if "incident_id" not in columns:
                connection.exec_driver_sql("ALTER TABLE dispatch_actions ADD COLUMN incident_id VARCHAR")
            volunteer_columns = {row[1] for row in connection.exec_driver_sql("PRAGMA table_info(volunteers)")}
            if "user_id" not in volunteer_columns:
                connection.exec_driver_sql("ALTER TABLE volunteers ADD COLUMN user_id VARCHAR")
            unlinked_volunteers = connection.exec_driver_sql(
                "SELECT id, name FROM volunteers WHERE user_id IS NULL"
            ).fetchall()
            for volunteer_id, volunteer_name in unlinked_volunteers:
                matching_users = connection.exec_driver_sql(
                    "SELECT id FROM users WHERE name = ? AND role = 'VOLUNTEER'",
                    (volunteer_name,),
                ).fetchall()
                if len(matching_users) != 1:
                    continue
                user_id = matching_users[0][0]
                already_linked = connection.exec_driver_sql(
                    "SELECT 1 FROM volunteers WHERE user_id = ? LIMIT 1",
                    (user_id,),
                ).first()
                if already_linked is None:
                    connection.exec_driver_sql(
                        "UPDATE volunteers SET user_id = ? WHERE id = ? AND user_id IS NULL",
                        (user_id, volunteer_id),
                    )
