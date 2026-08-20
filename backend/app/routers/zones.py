"""Zones router: GET /api/zones, GET /api/zones/{zone_id}, GET /api/map/zones."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import ZoneOut, ZoneDetailOut
from app.auth import require_roles

logger = logging.getLogger("resq-ai.zones")
router = APIRouter(prefix="/api", tags=["zones"])


@router.get("/zones", response_model=list[ZoneOut])
def list_zones(db: Session = Depends(get_db), user = Depends(require_roles("INCIDENT_COMMANDER"))):
    zones = db.query(models.RescueZone).order_by(models.RescueZone.risk_score.desc()).all()
    return zones


@router.get("/zones/{zone_id}", response_model=ZoneDetailOut)
def get_zone(zone_id: str, db: Session = Depends(get_db), user = Depends(require_roles("INCIDENT_COMMANDER"))):
    zone = db.query(models.RescueZone).filter(models.RescueZone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")

    active_incidents = (
        db.query(models.Incident)
        .filter(models.Incident.zone_id == zone_id, models.Incident.status == "ACTIVE")
        .count()
    )
    active_teams = (
        db.query(models.RescueTeam)
        .filter(models.RescueTeam.current_zone_id == zone_id, models.RescueTeam.status == "DEPLOYED")
        .count()
    )
    recent_reports = (
        db.query(models.SOSReport)
        .filter(models.SOSReport.zone_id == zone_id)
        .count()
    )

    return ZoneDetailOut(
        id=zone.id,
        name=zone.name,
        latitude=zone.latitude,
        longitude=zone.longitude,
        risk_score=zone.risk_score,
        people_at_risk=zone.people_at_risk,
        status=zone.status,
        color=zone.color,
        active_incidents=active_incidents,
        active_teams=active_teams,
        recent_reports=recent_reports,
    )


@router.get("/map/zones")
def map_zones(db: Session = Depends(get_db), user = Depends(require_roles("INCIDENT_COMMANDER"))):
    """Simple JSON structure suitable for feeding Leaflet markers directly."""
    zones = db.query(models.RescueZone).all()
    return {
        "zones": [
            {
                "id": z.id,
                "name": z.name,
                "latitude": z.latitude,
                "longitude": z.longitude,
                "risk_score": z.risk_score,
                "priority": (
                    "CRITICAL" if z.risk_score > 80 else
                    "HIGH" if z.risk_score > 60 else
                    "MEDIUM" if z.risk_score > 30 else "LOW"
                ),
                "people_at_risk": z.people_at_risk,
                "status": z.status,
                "color": z.color,
            }
            for z in zones
        ]
    }
