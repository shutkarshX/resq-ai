"""Shared pytest fixtures.

Each test run uses its own throwaway SQLite file so tests never touch your
real demo database (resq_ai.db) and can run repeatably in any order.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Point at an isolated test DB BEFORE importing app modules that read env.
os.environ["DATABASE_URL"] = "sqlite:///./test_resq_ai.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine, SessionLocal
from app import models
from app.risk_engine import calculate_risk


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Fresh schema before every test function."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    from main import app
    return TestClient(app)


@pytest.fixture
def seeded_client(client, db_session):
    """A client backed by a minimal, deterministic seeded DB (1 zone, 1 team)."""
    zone = models.RescueZone(
        id="Z-01", name="Riverside Colony", latitude=23.2599, longitude=77.4126,
        risk_score=96, people_at_risk=420, status="Immediate evacuation", color="#ff5f5f",
    )
    team = models.RescueTeam(
        id="TEAM-01", name="Alpha Water Rescue", team_type="Water Rescue",
        members=6, status="AVAILABLE",
    )
    db_session.add(zone)
    db_session.add(team)
    db_session.commit()
    return client
