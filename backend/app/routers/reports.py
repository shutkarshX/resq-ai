"""Reports router: POST /api/reports, GET /api/reports.

This is the core SOS -> Risk -> Incident pipeline described in the spec:
  1. Validate request (Pydantic does this).
  2. Calculate risk (risk_engine.calculate_risk).
  3. Create SOS report row.
  4. Create/update incident.
  5. Associate with nearest zone.
  6. Persist everything.
  7. Return the full result.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, services
from app.risk_engine import calculate_risk
from app.schemas import SOSReportIn, SOSReportAccepted, SOSReportOut

logger = logging.getLogger("resq-ai.reports")
router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/reports", response_model=SOSReportAccepted, status_code=201)
def create_report(payload: SOSReportIn, db: Session = Depends(get_db)):
    logger.info("SOS received: emergency=%s people=%s medical=%s",
                payload.emergency, payload.people, payload.medical_emergency)

    risk = calculate_risk(
        people=payload.people,
        flood_severity=payload.flood_severity,
        medical_emergency=payload.medical_emergency,
        infrastructure_damage=payload.infrastructure_damage,
        weather_severity=payload.weather_severity,
    )
    logger.info("Risk calculated: score=%s priority=%s", risk["risk_score"], risk["priority"])

    zone = services.find_nearest_zone(db, payload.latitude, payload.longitude)

    # Create the incident this report is associated with.
    incident = models.Incident(
        title=f"{payload.emergency} — {zone.name if zone else 'Unassigned zone'}",
        emergency_type=payload.emergency,
        description=f"Citizen-reported {payload.emergency.lower()} emergency via SOS channel.",
        latitude=payload.latitude,
        longitude=payload.longitude,
        people_at_risk=payload.people,
        medical_emergency=payload.medical_emergency,
        risk_score=risk["risk_score"],
        priority=risk["priority"],
        status="ACTIVE",
        zone_id=zone.id if zone else None,
    )
    db.add(incident)
    db.flush()  # get incident.id without committing yet

    report = models.SOSReport(
        emergency=payload.emergency,
        people=payload.people,
        medical_emergency=payload.medical_emergency,
        location=payload.location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        flood_severity=payload.flood_severity,
        infrastructure_damage=payload.infrastructure_damage,
        weather_severity=payload.weather_severity,
        risk_score=risk["risk_score"],
        priority=risk["priority"],
        status="NEW",
        zone_id=zone.id if zone else None,
        incident_id=incident.id,
        source="Citizen SOS",
        summary=f"{payload.emergency} emergency affecting an estimated {payload.people} people.",
    )
    db.add(report)

    if zone:
        services.refresh_zone_from_incident(db, zone)

    db.commit()
    db.refresh(report)
    db.refresh(incident)

    logger.info("SOS report %s stored, linked to incident %s / zone %s",
                report.id, incident.id, zone.id if zone else "none")

    return SOSReportAccepted(
        accepted=True,
        report_id=report.id,
        incident_id=incident.id,
        zone_id=zone.id if zone else None,
        risk_score=risk["risk_score"],
        priority=risk["priority"],
        message="SOS report received successfully",
    )


@router.get("/reports", response_model=list[SOSReportOut])
def list_reports(
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    zone_id: Optional[str] = Query(None),
    emergency: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    q = db.query(models.SOSReport)
    if priority:
        q = q.filter(models.SOSReport.priority == priority.upper())
    if status:
        q = q.filter(models.SOSReport.status == status.upper())
    if zone_id:
        q = q.filter(models.SOSReport.zone_id == zone_id)
    if emergency:
        q = q.filter(models.SOSReport.emergency.ilike(f"%{emergency}%"))

    reports = q.order_by(models.SOSReport.created_at.desc()).limit(limit).all()
    return reports
