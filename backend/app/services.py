"""Shared service-layer functions used by multiple routers.

Keeping this logic out of the routers avoids duplicated queries and keeps
dashboard numbers guaranteed to be computed the same way everywhere.
"""
import math
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models
from app.risk_engine import priority_color

logger = logging.getLogger("resq-ai.services")


# ---------- Dashboard metrics ----------

def compute_metrics(db: Session) -> dict:
    active_incidents = (
        db.query(func.count(models.Incident.id))
        .filter(models.Incident.status == "ACTIVE")
        .scalar()
        or 0
    )

    people_at_risk = (
        db.query(func.coalesce(func.sum(models.Incident.people_at_risk), 0))
        .filter(models.Incident.status == "ACTIVE")
        .scalar()
        or 0
    )

    teams_deployed = (
        db.query(func.count(models.RescueTeam.id))
        .filter(models.RescueTeam.status == "DEPLOYED")
        .scalar()
        or 0
    )

    teams_total = db.query(func.count(models.RescueTeam.id)).scalar() or 0

    cases_resolved = (
        db.query(func.count(models.DispatchAction.id))
        .filter(models.DispatchAction.status == "COMPLETED")
        .scalar()
        or 0
    )

    return {
        "active_incidents": int(active_incidents),
        "people_at_risk": int(people_at_risk),
        "teams_deployed": int(teams_deployed),
        "teams_total": int(teams_total),
        "cases_resolved": int(cases_resolved),
    }


def latest_ai_summary(db: Session) -> str:
    """Returns the most recent AI situation summary, or a sensible default
    if nothing has been analyzed yet."""
    latest = (
        db.query(models.AIAnalysis)
        .order_by(models.AIAnalysis.created_at.desc())
        .first()
    )
    if latest:
        return latest.situation_summary

    # Fall back to describing the highest-risk active zone.
    top_zone = (
        db.query(models.RescueZone)
        .order_by(models.RescueZone.risk_score.desc())
        .first()
    )
    if top_zone:
        return (
            f"{top_zone.name} shows the highest compounding risk in the current "
            f"incident, with {top_zone.people_at_risk} people estimated at risk "
            f"and a risk score of {top_zone.risk_score}/100."
        )
    return "No active incident data available yet."


def top_incident_name(db: Session) -> str:
    top_zone = (
        db.query(models.RescueZone)
        .order_by(models.RescueZone.risk_score.desc())
        .first()
    )
    if top_zone:
        return f"{top_zone.name} Response"
    return "RESQ-AI Response"


# ---------- Geo helpers ----------

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return r * c


def find_nearest_zone(db: Session, latitude: Optional[float], longitude: Optional[float], max_distance_km: float = 12.0) -> Optional[models.RescueZone]:
    """Find a response zone only when coordinates place the SOS nearby.

    A missing or distant coordinate must not silently turn into a report for
    the highest-risk demo zone.
    """
    zones = db.query(models.RescueZone).all()
    if not zones:
        return None

    if latitude is None or longitude is None:
        return None

    nearest = min(zones, key=lambda z: _haversine_km(latitude, longitude, z.latitude, z.longitude))
    return nearest if _haversine_km(latitude, longitude, nearest.latitude, nearest.longitude) <= max_distance_km else None


def create_response_zone(db: Session, location: Optional[str], latitude: Optional[float], longitude: Optional[float], risk_score: int, people_at_risk: int) -> models.RescueZone:
    """Create a coordinate-backed, non-demo response zone for an SOS outside known areas."""
    zone = models.RescueZone(
        id=models.new_id("Z-CIT"),
        name=location.strip() if location and location.strip() else "Citizen-reported location",
        latitude=latitude if latitude is not None else 0.0,
        longitude=longitude if longitude is not None else 0.0,
        risk_score=risk_score,
        people_at_risk=people_at_risk,
        status="Assessment required",
        color=priority_color("CRITICAL" if risk_score > 80 else "HIGH" if risk_score > 60 else "MEDIUM"),
    )
    db.add(zone)
    db.flush()
    return zone


# ---------- Team assignment ----------

def pick_available_team(db: Session, preferred_team_id: Optional[str] = None) -> Optional[models.RescueTeam]:
    if preferred_team_id:
        team = db.query(models.RescueTeam).filter(models.RescueTeam.id == preferred_team_id).first()
        return team  # caller validates availability

    return (
        db.query(models.RescueTeam)
        .filter(models.RescueTeam.status == "AVAILABLE")
        .order_by(models.RescueTeam.id)
        .first()
    )


# ---------- Zone status refresh ----------

def refresh_zone_from_incident(db: Session, zone: models.RescueZone):
    """Recompute a zone's risk_score/people_at_risk/color from its active
    incidents, so the map + dashboard stay consistent after new SOS reports."""
    active_incidents = (
        db.query(models.Incident)
        .filter(models.Incident.zone_id == zone.id, models.Incident.status == "ACTIVE")
        .all()
    )
    if not active_incidents:
        return

    zone.risk_score = max(i.risk_score for i in active_incidents)
    zone.people_at_risk = sum(i.people_at_risk for i in active_incidents)

    top_priority = max(active_incidents, key=lambda i: i.risk_score).priority
    zone.color = priority_color(top_priority)

    if top_priority == "CRITICAL":
        zone.status = "Immediate evacuation"
    elif top_priority == "HIGH":
        zone.status = "Rescue in progress"
    elif top_priority == "MEDIUM":
        zone.status = "Shelter activated"
    else:
        zone.status = "Monitoring"

    zone.updated_at = datetime.now(timezone.utc)
    db.add(zone)
