"""Volunteers router: GET/POST /api/volunteers, PATCH /api/volunteers/{id}."""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import require_roles
from app.schemas import (
    VolunteerOut, VolunteerCreateIn, VolunteerUpdateIn,
    VolunteerAssignmentCreateIn, VolunteerAssignmentOut,
    CommanderVolunteerAssignmentOut,
    WeatherLocationOut,
)
from app.weather import get_weather

logger = logging.getLogger("resq-ai.volunteers")
router = APIRouter(prefix="/api", tags=["volunteers"])


@router.get("/volunteer/me/weather", response_model=WeatherLocationOut)
def volunteer_weather(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("VOLUNTEER")),
):
    assignment = (
        db.query(models.VolunteerAssignment)
        .filter(
            models.VolunteerAssignment.volunteer_user_id == user.id,
            models.VolunteerAssignment.status != "COMPLETED",
        )
        .order_by(models.VolunteerAssignment.created_at.desc())
        .first()
    )
    if not assignment or not assignment.action:
        raise HTTPException(status_code=404, detail="No active operational location available")
    zone = db.query(models.RescueZone).filter(models.RescueZone.id == assignment.action.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Operational location unavailable")
    weather = get_weather(zone.latitude, zone.longitude)
    if weather is None:
        raise HTTPException(status_code=503, detail="Weather data unavailable")
    return {**weather, "location_name": zone.name}


@router.get("/volunteers", response_model=list[VolunteerOut])
def list_volunteers(db: Session = Depends(get_db), user: models.User = Depends(require_roles("INCIDENT_COMMANDER"))):
    return db.query(models.Volunteer).order_by(models.Volunteer.name).all()


@router.post("/volunteers", response_model=VolunteerOut, status_code=201)
def create_volunteer(
    payload: VolunteerCreateIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("INCIDENT_COMMANDER")),
):
    volunteer = models.Volunteer(
        name=payload.name,
        skills=payload.skills,
        location=payload.location,
        availability="AVAILABLE",
        status="AVAILABLE",
    )
    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    logger.info("New volunteer registered: %s (%s)", volunteer.id, volunteer.name)
    return volunteer


@router.patch("/volunteers/{volunteer_id}", response_model=VolunteerOut)
def update_volunteer(
    volunteer_id: str,
    payload: VolunteerUpdateIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("INCIDENT_COMMANDER")),
):
    volunteer = db.query(models.Volunteer).filter(models.Volunteer.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail=f"Volunteer '{volunteer_id}' not found")

    if payload.status:
        volunteer.status = payload.status
    if payload.availability:
        volunteer.availability = payload.availability
    if payload.skills is not None:
        volunteer.skills = payload.skills
    if payload.location is not None:
        volunteer.location = payload.location

    db.add(volunteer)
    db.commit()
    db.refresh(volunteer)
    logger.info("Volunteer %s updated (status=%s)", volunteer.id, volunteer.status)
    return volunteer


@router.post("/volunteer-assignments", response_model=VolunteerAssignmentOut, status_code=201)
def assign_volunteer(
    payload: VolunteerAssignmentCreateIn,
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("INCIDENT_COMMANDER")),
):
    volunteer_record = db.query(models.Volunteer).filter(models.Volunteer.id == payload.volunteer_id).first()
    volunteer = db.query(models.User).filter(
        models.User.id == volunteer_record.user_id if volunteer_record else False,
        models.User.role == "VOLUNTEER",
    ).first()
    action = db.query(models.DispatchAction).filter(models.DispatchAction.id == payload.action_id).first()
    if not volunteer or not action:
        raise HTTPException(status_code=404, detail="Volunteer or operation not found")
    if volunteer_record.status != "AVAILABLE":
        raise HTTPException(status_code=409, detail="Volunteer is not available")
    assignment = models.VolunteerAssignment(
        volunteer_user_id=volunteer.id, action_id=action.id, instructions=payload.instructions,
    )
    volunteer_record.status = "ASSIGNED"
    volunteer_record.availability = "ASSIGNED"
    db.add(volunteer_record)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/volunteer-assignments", response_model=list[CommanderVolunteerAssignmentOut])
def list_volunteer_assignments(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("INCIDENT_COMMANDER")),
):
    assignments = (
        db.query(models.VolunteerAssignment)
        .join(models.User, models.User.id == models.VolunteerAssignment.volunteer_user_id)
        .order_by(models.VolunteerAssignment.created_at.desc())
        .all()
    )
    volunteer_records = {
        record.user_id: record
        for record in db.query(models.Volunteer).filter(models.Volunteer.user_id.isnot(None)).all()
    }
    return [
        CommanderVolunteerAssignmentOut(
            id=assignment.id,
            action_id=assignment.action_id,
            instructions=assignment.instructions,
            status=assignment.status,
            created_at=assignment.created_at,
            completed_at=assignment.completed_at,
            action=assignment.action,
            volunteer_id=volunteer_records[assignment.volunteer_user_id].id,
            volunteer_name=volunteer.name,
            volunteer_skills=volunteer_records[assignment.volunteer_user_id].skills,
            volunteer_location=volunteer_records[assignment.volunteer_user_id].location,
        )
        for assignment in assignments
        if assignment.volunteer_user_id in volunteer_records
        for volunteer in [db.query(models.User).filter(models.User.id == assignment.volunteer_user_id).first()]
        if volunteer is not None
    ]


@router.get("/volunteer/me/assignments", response_model=list[VolunteerAssignmentOut])
def my_assignments(
    db: Session = Depends(get_db), user: models.User = Depends(require_roles("VOLUNTEER")),
):
    return db.query(models.VolunteerAssignment).filter(
        models.VolunteerAssignment.volunteer_user_id == user.id
    ).order_by(models.VolunteerAssignment.created_at.desc()).all()


@router.patch("/volunteer/me/assignments/{assignment_id}/accept", response_model=VolunteerAssignmentOut)
def accept_assignment(assignment_id: str, db: Session = Depends(get_db), user: models.User = Depends(require_roles("VOLUNTEER"))):
    assignment = db.query(models.VolunteerAssignment).filter(models.VolunteerAssignment.id == assignment_id, models.VolunteerAssignment.volunteer_user_id == user.id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.status = "IN_PROGRESS"
    if assignment.action.status in {"QUEUED", "DEPLOYED"}:
        assignment.action.status = "IN_PROGRESS"
    db.commit()
    db.refresh(assignment)
    return assignment


@router.patch("/volunteer/me/assignments/{assignment_id}/complete", response_model=VolunteerAssignmentOut)
def complete_assignment(
    assignment_id: str,
    db: Session = Depends(get_db), user: models.User = Depends(require_roles("VOLUNTEER")),
):
    assignment = db.query(models.VolunteerAssignment).filter(
        models.VolunteerAssignment.id == assignment_id,
        models.VolunteerAssignment.volunteer_user_id == user.id,
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    assignment.status = "COMPLETED"
    assignment.completed_at = datetime.now(timezone.utc)
    remaining = db.query(models.VolunteerAssignment).filter(
        models.VolunteerAssignment.action_id == assignment.action_id,
        models.VolunteerAssignment.id != assignment.id,
        models.VolunteerAssignment.status != "COMPLETED",
    ).count()
    if remaining == 0:
        assignment.action.status = "COMPLETED"
        assignment.action.completed_at = datetime.now(timezone.utc)
        if assignment.action.team_id:
            team = db.query(models.RescueTeam).filter(models.RescueTeam.id == assignment.action.team_id).first()
            if team:
                team.status, team.current_zone_id = "AVAILABLE", None
        if assignment.action.report_id:
            report = db.query(models.SOSReport).filter(models.SOSReport.id == assignment.action.report_id).first()
            if report:
                report.status = "RESOLVED"
                incident = db.query(models.Incident).filter(models.Incident.id == report.incident_id).first()
                if incident:
                    incident.status = "RESOLVED"
    record = db.query(models.Volunteer).filter(models.Volunteer.user_id == user.id).first()
    if record:
        record.status, record.availability = "AVAILABLE", "AVAILABLE"
    db.commit()
    db.refresh(assignment)
    return assignment
