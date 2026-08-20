"""Teams router: GET /api/teams, GET /api/teams/available."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import TeamOut, TeamCreateIn
from app.auth import require_roles

logger = logging.getLogger("resq-ai.teams")
router = APIRouter(prefix="/api", tags=["teams"])


@router.get("/teams", response_model=list[TeamOut])
def list_teams(db: Session = Depends(get_db), user: models.User = Depends(require_roles("INCIDENT_COMMANDER"))):
    return db.query(models.RescueTeam).order_by(models.RescueTeam.id).all()


@router.get("/teams/available", response_model=list[TeamOut])
def list_available_teams(db: Session = Depends(get_db), user: models.User = Depends(require_roles("INCIDENT_COMMANDER"))):
    return (
        db.query(models.RescueTeam)
        .filter(models.RescueTeam.status == "AVAILABLE")
        .order_by(models.RescueTeam.id)
        .all()
    )


@router.post("/teams", response_model=TeamOut, status_code=201)
def create_team(payload: TeamCreateIn, db: Session = Depends(get_db), user: models.User = Depends(require_roles("INCIDENT_COMMANDER"))):
    # Generate the next TEAM-XX id.
    existing = db.query(models.RescueTeam).count()
    team_id = f"TEAM-{existing + 1:02d}"
    while db.query(models.RescueTeam).filter(models.RescueTeam.id == team_id).first():
        existing += 1
        team_id = f"TEAM-{existing + 1:02d}"

    team = models.RescueTeam(
        id=team_id,
        name=payload.name,
        team_type=payload.team_type,
        members=payload.members,
        status="AVAILABLE",
    )
    db.add(team)
    db.commit()
    db.refresh(team)
    logger.info("Created new rescue team %s (%s)", team.id, team.name)
    return team


@router.get("/teams/{team_id}", response_model=TeamOut)
def get_team(team_id: str, db: Session = Depends(get_db), user: models.User = Depends(require_roles("INCIDENT_COMMANDER"))):
    team = db.query(models.RescueTeam).filter(models.RescueTeam.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team '{team_id}' not found")
    return team
