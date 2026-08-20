"""Commander-only user and activity views."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.auth import require_roles
from app.database import get_db
from app.schemas import (
    ActivityEventOut,
    CitizenActivityOut,
    UserManagementOut,
    UserManagementPayload,
)

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=UserManagementPayload)
def list_users(
    db: Session = Depends(get_db),
    user: models.User = Depends(require_roles("INCIDENT_COMMANDER")),
):
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    volunteer_records = {
        volunteer.user_id: volunteer
        for volunteer in db.query(models.Volunteer).filter(models.Volunteer.user_id.isnot(None)).all()
    }
    assignments = db.query(models.VolunteerAssignment).order_by(models.VolunteerAssignment.created_at.desc()).all()

    user_rows = []
    activity = []
    for account in users:
        volunteer = volunteer_records.get(account.id)
        account_assignments = [assignment for assignment in assignments if assignment.volunteer_user_id == account.id]
        active_assignments = [assignment for assignment in account_assignments if assignment.status != "COMPLETED"]
        completed_assignments = [assignment for assignment in account_assignments if assignment.status == "COMPLETED"]
        current = active_assignments[0] if active_assignments else None
        user_rows.append(UserManagementOut(
            id=account.id,
            name=account.name,
            email=account.email,
            role=account.role,
            created_at=account.created_at,
            volunteer_id=volunteer.id if volunteer else None,
            volunteer_status=volunteer.status if volunteer else None,
            volunteer_availability=volunteer.availability if volunteer else None,
            volunteer_skills=volunteer.skills if volunteer else None,
            volunteer_location=volunteer.location if volunteer else None,
            assignment_count=len(account_assignments),
            active_assignment_count=len(active_assignments),
            completed_assignment_count=len(completed_assignments),
            current_assignment=current.action.action if current else None,
        ))
        for assignment in account_assignments:
            activity.append(ActivityEventOut(
                label=f"{account.name} assigned to {assignment.action.action}",
                category="assignment",
                timestamp=assignment.created_at,
            ))
            if assignment.status == "COMPLETED" and assignment.completed_at:
                activity.append(ActivityEventOut(
                    label=f"{account.name} completed {assignment.action.action}",
                    category="assignment",
                    timestamp=assignment.completed_at,
                ))

    reports = db.query(models.SOSReport).order_by(models.SOSReport.created_at.desc()).limit(100).all()
    citizen_sos = []
    for report in reports:
        action = (
            db.query(models.DispatchAction)
            .filter(models.DispatchAction.report_id == report.id)
            .order_by(models.DispatchAction.created_at.desc())
            .first()
        )
        zone_name = report.zone.name if report.zone else None
        citizen_sos.append(CitizenActivityOut(
            report_id=report.id,
            emergency=report.emergency,
            location=report.location,
            zone_name=zone_name,
            people=report.people,
            priority=report.priority,
            status=report.status,
            created_at=report.created_at,
            response_status=action.status if action else None,
        ))
        if action and action.completed_at:
            activity.append(ActivityEventOut(
                label=f"{report.id} response completed",
                category="citizen_sos",
                timestamp=action.completed_at,
            ))
        if report.incident and report.incident.status == "RESOLVED":
            activity.append(ActivityEventOut(
                label=f"Incident for {report.id} marked resolved",
                category="incident",
                timestamp=report.incident.updated_at or report.created_at,
            ))

    return UserManagementPayload(
        users=user_rows,
        citizen_sos=citizen_sos,
        activity=sorted(activity, key=lambda event: event.timestamp, reverse=True)[:100],
    )