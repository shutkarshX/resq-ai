"""Dashboard router: GET /api/dashboard.

This is the endpoint the EXISTING frontend already calls on startup and
every 30 seconds (see src/api.ts -> resqApi.dashboard()). The response
shape here matches DashboardPayload exactly so no frontend changes are
required.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, services
from app.schemas import DashboardOut, IncidentSummary, MetricsOut, ZoneOut

logger = logging.getLogger("resq-ai.dashboard")
router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    metrics = services.compute_metrics(db)
    zones = db.query(models.RescueZone).order_by(models.RescueZone.risk_score.desc()).all()
    ai_summary = services.latest_ai_summary(db)
    incident_name = services.top_incident_name(db)

    top_zone = zones[0] if zones else None
    severity = "critical"
    if top_zone:
        if top_zone.risk_score > 80:
            severity = "critical"
        elif top_zone.risk_score > 60:
            severity = "high"
        elif top_zone.risk_score > 30:
            severity = "medium"
        else:
            severity = "low"

    logger.info("Dashboard requested — %s active incidents, %s people at risk",
                metrics["active_incidents"], metrics["people_at_risk"])

    return DashboardOut(
        incident=IncidentSummary(
            name=incident_name,
            severity=severity,
            updated_at=datetime.now(timezone.utc).isoformat(),
        ),
        metrics=MetricsOut(**metrics),
        zones=[ZoneOut.model_validate(z) for z in zones],
        ai_summary=ai_summary,
    )
