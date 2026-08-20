"""Public, citizen-safe data endpoints.

These intentionally expose only report status, public shelters, and concise
area alerts. Internal reports, teams, and operations remain commander-only.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import PublicSOSStatusOut, ShelterOut, CitizenAlertOut, WeatherOut
from app.weather import get_weather

router = APIRouter(prefix="/api/public", tags=["citizen"])


@router.get("/weather", response_model=WeatherOut)
def current_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    weather = get_weather(latitude, longitude)
    if weather is None:
        raise HTTPException(status_code=503, detail="Weather data unavailable")
    return weather


@router.get("/reports/{report_id}", response_model=PublicSOSStatusOut)
def track_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(models.SOSReport).filter(models.SOSReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="SOS report not found")
    action = db.query(models.DispatchAction).filter(models.DispatchAction.report_id == report.id).order_by(models.DispatchAction.created_at.desc()).first()
    messages = {
        "NEW": "Your emergency report has been received and is being reviewed.",
        "TRIAGED": "Your report has been reviewed and is being prioritized by the response team.",
        "RESOLVED": "This report has been marked resolved. If you still need help, submit a new SOS.",
    }
    response_summary = None
    response_status = None
    if action:
        response_status = action.status
        if action.status == "QUEUED":
            response_summary = "A response operation has been assigned and is awaiting deployment."
        elif action.status == "DEPLOYED":
            response_summary = "A response team has been deployed and is progressing to your area."
        elif action.status == "IN_PROGRESS":
            response_summary = "Responders are actively working on this emergency."
        elif action.status == "COMPLETED":
            response_summary = "The response operation has been completed."
    return PublicSOSStatusOut(
        report_id=report.id, emergency=report.emergency, location=report.location,
        priority=report.priority, status=report.status, created_at=report.created_at,
        message=messages.get(report.status, "Your report is being reviewed."),
        response_status=response_status, response_summary=response_summary,
    )


@router.get("/shelters", response_model=list[ShelterOut])
def list_shelters(db: Session = Depends(get_db)):
    return db.query(models.Shelter).order_by(models.Shelter.name).all()


@router.get("/alerts", response_model=list[CitizenAlertOut])
def list_alerts(db: Session = Depends(get_db)):
    zones = db.query(models.RescueZone).order_by(models.RescueZone.risk_score.desc()).all()
    alerts = []
    for zone in zones:
        severity = "CRITICAL" if zone.risk_score > 80 else "HIGH" if zone.risk_score > 60 else "MEDIUM"
        incident = (
            db.query(models.Incident)
            .filter(
                models.Incident.zone_id == zone.id,
                models.Incident.status == "ACTIVE",
            )
            .order_by(models.Incident.created_at.desc())
            .first()
        )
        action = (
            db.query(models.DispatchAction)
            .filter(
                models.DispatchAction.zone_id == zone.id,
                models.DispatchAction.status != "CANCELLED",
            )
            .order_by(models.DispatchAction.created_at.desc())
            .first()
        )

        response_messages = {
            "QUEUED": "A response has been requested and is awaiting deployment.",
            "DEPLOYED": "A response team has been deployed to the area.",
            "IN_PROGRESS": "Responders are actively working in the area.",
            "COMPLETED": "The latest response operation has been completed.",
        }
        response_message = response_messages.get(action.status) if action else None

        if incident:
            title = f"{incident.emergency_type} emergency — {zone.name}"
            people_context = (
                f" An estimated {incident.people_at_risk} people are currently at risk."
                if incident.people_at_risk > 0
                else ""
            )
            incident_context = incident.description or "An active emergency has been reported in this area."
            response_context = f" {response_message}" if response_message else " Response coordination is pending."
            action_context = (
                " Follow evacuation instructions and move to a safe location if advised."
                if severity in {"CRITICAL", "HIGH"}
                else " Avoid the affected area where possible and follow local authority guidance."
            )
            message = f"{incident_context}{people_context}{response_context}{action_context}"
        elif response_message:
            title = f"Response underway — {zone.name}"
            message = f"{response_message} Current area status: {zone.status}. Follow local authority guidance."
        else:
            title = f"{severity.title()} area alert — {zone.name}"
            message = (
                f"Current area status: {zone.status}. Approximately {zone.people_at_risk} people are at risk. "
                "Follow local authority instructions and move to a safe location if advised."
            )

        alerts.append(CitizenAlertOut(
            id=f"zone-{zone.id}", severity=severity, zone_name=zone.name,
            title=title,
            message=message,
        ))
    return alerts
