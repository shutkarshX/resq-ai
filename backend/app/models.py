"""SQLAlchemy ORM models.

IDs are human-readable strings (e.g. "Z-01", "TEAM-03") to match the
existing frontend's zone IDs and to keep Swagger/demo testing readable.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


class RescueZone(Base):
    __tablename__ = "rescue_zones"

    id = Column(String, primary_key=True)  # e.g. "Z-01"
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    risk_score = Column(Integer, nullable=False, default=0)
    people_at_risk = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default="Monitoring")
    color = Column(String, nullable=False, default="#ffd166")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    incidents = relationship("Incident", back_populates="zone")
    teams = relationship("RescueTeam", back_populates="current_zone")
    actions = relationship("DispatchAction", back_populates="zone")


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, default=lambda: new_id("INC"))
    title = Column(String, nullable=False)
    emergency_type = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    people_at_risk = Column(Integer, nullable=False, default=0)
    medical_emergency = Column(Boolean, nullable=False, default=False)
    risk_score = Column(Integer, nullable=False, default=0)
    priority = Column(String, nullable=False, default="LOW")
    status = Column(String, nullable=False, default="ACTIVE")  # ACTIVE, RESOLVED
    zone_id = Column(String, ForeignKey("rescue_zones.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    zone = relationship("RescueZone", back_populates="incidents")
    reports = relationship("SOSReport", back_populates="incident")
    ai_analyses = relationship("AIAnalysis", back_populates="incident")


class SOSReport(Base):
    __tablename__ = "sos_reports"

    id = Column(String, primary_key=True, default=lambda: new_id("SOS"))
    emergency = Column(String, nullable=False)
    people = Column(Integer, nullable=False, default=0)
    medical_emergency = Column(Boolean, nullable=False, default=False)
    location = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    flood_severity = Column(Integer, nullable=False, default=0)
    infrastructure_damage = Column(Integer, nullable=False, default=0)
    weather_severity = Column(Integer, nullable=False, default=0)
    risk_score = Column(Integer, nullable=False, default=0)
    priority = Column(String, nullable=False, default="LOW")
    status = Column(String, nullable=False, default="NEW")  # NEW, TRIAGED, RESOLVED
    zone_id = Column(String, ForeignKey("rescue_zones.id"), nullable=True)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)
    source = Column(String, nullable=False, default="Citizen SOS")
    summary = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    zone = relationship("RescueZone")
    incident = relationship("Incident", back_populates="reports")


class RescueTeam(Base):
    __tablename__ = "rescue_teams"

    id = Column(String, primary_key=True)  # e.g. "TEAM-01"
    name = Column(String, nullable=False)
    team_type = Column(String, nullable=False)  # e.g. "Water Rescue", "Medical"
    members = Column(Integer, nullable=False, default=4)
    status = Column(String, nullable=False, default="AVAILABLE")
    current_zone_id = Column(String, ForeignKey("rescue_zones.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    current_zone = relationship("RescueZone", back_populates="teams")
    actions = relationship("DispatchAction", back_populates="team")


class DispatchAction(Base):
    __tablename__ = "dispatch_actions"

    id = Column(String, primary_key=True, default=lambda: new_id("ACT"))
    zone_id = Column(String, ForeignKey("rescue_zones.id"), nullable=False)
    team_id = Column(String, ForeignKey("rescue_teams.id"), nullable=True)
    action = Column(String, nullable=False)
    status = Column(String, nullable=False, default="QUEUED")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    zone = relationship("RescueZone", back_populates="actions")
    team = relationship("RescueTeam", back_populates="actions")


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(String, primary_key=True, default=lambda: new_id("VOL"))
    name = Column(String, nullable=False)
    skills = Column(String, nullable=True)  # comma-separated for simplicity
    availability = Column(String, nullable=False, default="AVAILABLE")
    location = Column(String, nullable=True)
    status = Column(String, nullable=False, default="AVAILABLE")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(String, primary_key=True, default=lambda: new_id("AI"))
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)
    situation_summary = Column(Text, nullable=False)
    recommendations = Column(Text, nullable=False)  # JSON-encoded list
    confidence = Column(Float, nullable=False, default=0.8)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    incident = relationship("Incident", back_populates="ai_analyses")
