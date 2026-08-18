"""Deterministic disaster risk scoring engine.

This is intentionally NOT AI-driven. The numeric risk score must be
reproducible and auditable, since it drives prioritization and dispatch.
The AI layer (ai_engine.py) only explains/recommends — it never sets
the score.

Point allocation (max 100):
    people_at_risk        -> up to 30
    flood_severity         -> up to 25 (input is already 0-25)
    medical_emergency      -> 20 (flat, boolean)
    infrastructure_damage  -> up to 15 (input is already 0-15)
    weather_severity       -> up to 10 (input is already 0-10)
"""
from typing import TypedDict


class RiskBreakdown(TypedDict):
    people: int
    flood: int
    medical: int
    infrastructure: int
    weather: int


class RiskResult(TypedDict):
    risk_score: int
    priority: str
    breakdown: RiskBreakdown


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def score_people_at_risk(people: int) -> int:
    """0-30 points. Scales with headcount; saturates at 500+ people."""
    if people <= 0:
        return 0
    # Linear scale: 500 people -> full 30 points.
    points = round((people / 500) * 30)
    return _clamp(points, 0, 30)


def calculate_risk(
    people: int,
    flood_severity: int,
    medical_emergency: bool,
    infrastructure_damage: int,
    weather_severity: int,
) -> RiskResult:
    people_pts = score_people_at_risk(people)
    flood_pts = _clamp(int(flood_severity), 0, 25)
    medical_pts = 20 if medical_emergency else 0
    infra_pts = _clamp(int(infrastructure_damage), 0, 15)
    weather_pts = _clamp(int(weather_severity), 0, 10)

    total = people_pts + flood_pts + medical_pts + infra_pts + weather_pts
    total = _clamp(total, 0, 100)

    if total <= 30:
        priority = "LOW"
    elif total <= 60:
        priority = "MEDIUM"
    elif total <= 80:
        priority = "HIGH"
    else:
        priority = "CRITICAL"

    return {
        "risk_score": total,
        "priority": priority,
        "breakdown": {
            "people": people_pts,
            "flood": flood_pts,
            "medical": medical_pts,
            "infrastructure": infra_pts,
            "weather": weather_pts,
        },
    }


def priority_color(priority: str) -> str:
    """Maps a priority level to the color scheme already used by the frontend."""
    return {
        "CRITICAL": "#ff5f5f",
        "HIGH": "#ffb547",
        "MEDIUM": "#ffd166",
        "LOW": "#8fd6a6",
    }.get(priority, "#ffd166")
