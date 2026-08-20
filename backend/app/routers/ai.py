"""AI router: POST /api/ai/analyze, POST /api/ai/response-plan.

SAFETY: All output here is advisory-only decision support. See
app/ai_engine.py for the safety contract and ADVISORY_NOTICE text that is
attached to every response.
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.ai_engine import analyze_incident, build_response_plan
from app.risk_engine import calculate_risk
from app.schemas import AIAnalyzeIn, AIAnalyzeOut, ResponsePlanIn, ResponsePlanOut
from app.auth import require_roles

logger = logging.getLogger("resq-ai.ai")
router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/analyze", response_model=AIAnalyzeOut)
def ai_analyze(payload: AIAnalyzeIn, db: Session = Depends(get_db), user: models.User = Depends(require_roles("INCIDENT_COMMANDER"))):
    risk_score = payload.risk_score
    priority = payload.priority

    incident = None
    if payload.incident_id:
        incident = db.query(models.Incident).filter(models.Incident.id == payload.incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail=f"Incident '{payload.incident_id}' not found")
        # Trust the deterministic risk engine's stored values over caller input.
        risk_score = incident.risk_score
        priority = incident.priority

    if risk_score is None or priority is None:
        # No incident and no risk supplied — compute a reasonable default
        # from the given fields so this endpoint remains usable standalone.
        computed = calculate_risk(
            people=payload.people,
            flood_severity=15 if "flood" in payload.emergency.lower() else 5,
            medical_emergency=payload.medical_emergency,
            infrastructure_damage=5,
            weather_severity=5,
        )
        risk_score = computed["risk_score"]
        priority = computed["priority"]

    result = analyze_incident(
        emergency=payload.emergency,
        people=payload.people,
        medical_emergency=payload.medical_emergency,
        risk_score=risk_score,
        priority=priority,
        weather=payload.weather,
        area=payload.area,
    )

    # Persist the analysis for dashboard "AI summary" and audit trail.
    analysis = models.AIAnalysis(
        incident_id=incident.id if incident else None,
        situation_summary=result["situation"],
        recommendations=json.dumps(result["recommendations"]),
        confidence=result["confidence"],
    )
    db.add(analysis)
    db.commit()

    logger.info("AI analysis generated for incident=%s priority=%s confidence=%s",
                incident.id if incident else "none", priority, result["confidence"])

    return AIAnalyzeOut(**result)


@router.post("/response-plan", response_model=ResponsePlanOut)
def ai_response_plan(payload: ResponsePlanIn, db: Session = Depends(get_db), user: models.User = Depends(require_roles("INCIDENT_COMMANDER"))):
    zone = db.query(models.RescueZone).filter(models.RescueZone.id == payload.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail=f"Zone '{payload.zone_id}' not found")

    priority = (
        "CRITICAL" if zone.risk_score > 80 else
        "HIGH" if zone.risk_score > 60 else
        "MEDIUM" if zone.risk_score > 30 else "LOW"
    )

    plan = build_response_plan(
        zone_name=zone.name,
        zone_id=zone.id,
        risk_score=zone.risk_score,
        priority=priority,
        people_at_risk=zone.people_at_risk,
        zone_status=zone.status,
    )

    logger.info("Response plan generated for zone %s (priority=%s)", zone.id, priority)

    return ResponsePlanOut(**plan)
