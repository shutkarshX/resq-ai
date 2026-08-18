"""Actions router: POST /api/actions/assign, GET /api/actions,
GET /api/actions/{id}, PATCH /api/actions/{id}.

POST /api/actions/assign is the second endpoint the EXISTING frontend
already calls (see src/api.ts -> resqApi.assign()). The request/response
shape is backward compatible: the old frontend only sends {zone_id, action}
and ignores extra response fields, so adding team_id/status here is safe.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, services
from app.schemas import (
    ActionAssignIn, ActionAssignOut, ActionOut, ActionStatusUpdateIn
)

logger = logging.getLogger("resq-ai.actions")
router = APIRouter(prefix="/api", tags=["actions"])


@router.post("/actions/assign", response_model=ActionAssignOut, status_code=201)
def assign_action(payload: ActionAssignIn, db: Session = Depends(get_db)):
    zone = db.query(models.RescueZone).filter(models.RescueZone.id == payload.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{payload.zone_id}' not found")

    team = services.pick_available_team(db, preferred_team_id=payload.team_id)

    if payload.team_id and team is None:
        raise HTTPException(status_code=404, detail=f"Team '{payload.team_id}' not found")

    if team is not None and team.status != "AVAILABLE":
        raise HTTPException(
            status_code=409,
            detail=f"Team '{team.id}' is not available (current status: {team.status})",
        )

    action = models.DispatchAction(
        zone_id=zone.id,
        team_id=team.id if team else None,
        action=payload.action,
        status="DEPLOYED" if team else "QUEUED",
    )
    db.add(action)

    if team:
        team.status = "DEPLOYED"
        team.current_zone_id = zone.id
        team.updated_at = datetime.now(timezone.utc)
        db.add(team)
        logger.info("Team %s deployed to zone %s for action '%s'", team.id, zone.id, payload.action)
    else:
        logger.info("Action '%s' queued for zone %s (no available team)", payload.action, zone.id)

    db.commit()
    db.refresh(action)

    return ActionAssignOut(
        accepted=True,
        action_id=action.id,
        team_id=team.id if team else None,
        zone_id=zone.id,
        status=action.status,
        message="Team deployed successfully" if team else "Action queued for dispatch (no team currently available)",
        queued_at=action.created_at.isoformat(),
    )


@router.get("/actions", response_model=list[ActionOut])
def list_actions(db: Session = Depends(get_db)):
    return db.query(models.DispatchAction).order_by(models.DispatchAction.created_at.desc()).all()


@router.get("/actions/{action_id}", response_model=ActionOut)
def get_action(action_id: str, db: Session = Depends(get_db)):
    action = db.query(models.DispatchAction).filter(models.DispatchAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
    return action


@router.patch("/actions/{action_id}", response_model=ActionOut)
def update_action_status(action_id: str, payload: ActionStatusUpdateIn, db: Session = Depends(get_db)):
    action = db.query(models.DispatchAction).filter(models.DispatchAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")

    action.status = payload.status

    if payload.status == "COMPLETED":
        action.completed_at = datetime.now(timezone.utc)

        # Free up the team.
        if action.team_id:
            team = db.query(models.RescueTeam).filter(models.RescueTeam.id == action.team_id).first()
            if team:
                team.status = "AVAILABLE"
                team.current_zone_id = None
                team.updated_at = datetime.now(timezone.utc)
                db.add(team)
                logger.info("Team %s completed action %s, now AVAILABLE", team.id, action.id)

        # Resolve the most recently linked active incident for this zone, if any.
        incident = (
            db.query(models.Incident)
            .filter(models.Incident.zone_id == action.zone_id, models.Incident.status == "ACTIVE")
            .order_by(models.Incident.created_at.desc())
            .first()
        )
        if incident:
            incident.status = "RESOLVED"
            incident.updated_at = datetime.now(timezone.utc)
            db.add(incident)
            logger.info("Incident %s marked RESOLVED after action %s completion", incident.id, action.id)

        zone = db.query(models.RescueZone).filter(models.RescueZone.id == action.zone_id).first()
        if zone:
            zone.status = "Monitoring"
            zone.updated_at = datetime.now(timezone.utc)
            db.add(zone)

    elif payload.status == "CANCELLED":
        if action.team_id:
            team = db.query(models.RescueTeam).filter(models.RescueTeam.id == action.team_id).first()
            if team and team.status == "DEPLOYED":
                team.status = "AVAILABLE"
                team.current_zone_id = None
                team.updated_at = datetime.now(timezone.utc)
                db.add(team)
                logger.info("Team %s freed after action %s cancellation", team.id, action.id)

    db.add(action)
    db.commit()
    db.refresh(action)

    logger.info("Action %s status updated to %s", action.id, payload.status)
    return action
