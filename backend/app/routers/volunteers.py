"""Volunteers router: GET/POST /api/volunteers, PATCH /api/volunteers/{id}."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.schemas import VolunteerOut, VolunteerCreateIn, VolunteerUpdateIn

logger = logging.getLogger("resq-ai.volunteers")
router = APIRouter(prefix="/api", tags=["volunteers"])


@router.get("/volunteers", response_model=list[VolunteerOut])
def list_volunteers(db: Session = Depends(get_db)):
    return db.query(models.Volunteer).order_by(models.Volunteer.name).all()


@router.post("/volunteers", response_model=VolunteerOut, status_code=201)
def create_volunteer(payload: VolunteerCreateIn, db: Session = Depends(get_db)):
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
def update_volunteer(volunteer_id: str, payload: VolunteerUpdateIn, db: Session = Depends(get_db)):
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
