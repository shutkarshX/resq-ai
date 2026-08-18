"""Search router: GET /api/search?q=..."""
import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import SearchResults, ZoneOut, IncidentOut, SOSReportOut, TeamOut

logger = logging.getLogger("resq-ai.search")
router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResults)
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    like = f"%{q}%"

    zones = (
        db.query(models.RescueZone)
        .filter(models.RescueZone.name.ilike(like))
        .limit(20)
        .all()
    )
    incidents = (
        db.query(models.Incident)
        .filter(
            (models.Incident.title.ilike(like))
            | (models.Incident.emergency_type.ilike(like))
        )
        .limit(20)
        .all()
    )
    reports = (
        db.query(models.SOSReport)
        .filter(
            (models.SOSReport.emergency.ilike(like))
            | (models.SOSReport.location.ilike(like))
        )
        .limit(20)
        .all()
    )
    teams = (
        db.query(models.RescueTeam)
        .filter(
            (models.RescueTeam.name.ilike(like))
            | (models.RescueTeam.team_type.ilike(like))
        )
        .limit(20)
        .all()
    )

    logger.info("Search '%s' -> %d zones, %d incidents, %d reports, %d teams",
                q, len(zones), len(incidents), len(reports), len(teams))

    return SearchResults(
        zones=[ZoneOut.model_validate(z) for z in zones],
        incidents=[IncidentOut.model_validate(i) for i in incidents],
        reports=[SOSReportOut.model_validate(r) for r in reports],
        teams=[TeamOut.model_validate(t) for t in teams],
    )
