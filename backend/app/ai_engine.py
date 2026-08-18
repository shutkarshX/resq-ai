"""AI decision-support engine.

SAFETY CONTRACT:
This module (and everything downstream of it) produces ADVISORY TEXT ONLY.
It must never claim to have dispatched real emergency services, contacted
police/fire/ambulance, evacuated real people, or controlled any real-world
system. All output is a recommendation for a human operator to review.

If OPENAI_API_KEY is set, we *could* call an external model to phrase the
summary more richly, but the hackathon requirement is that the system must
work perfectly with NO external API key. So this module ships a fully
deterministic fallback engine that is used by default, and is good enough
to be the primary path (not just a degraded fallback).
"""
import os
from typing import Optional, List, Dict


ADVISORY_NOTICE = (
    "This is AI decision-support only. No real-world dispatch, evacuation, "
    "or emergency contact has occurred. A human operator must review and "
    "execute all actions."
)


def _has_external_ai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def _situation_summary(
    emergency: str,
    people: int,
    medical_emergency: bool,
    priority: str,
    weather: Optional[str],
    area: Optional[str],
) -> str:
    area_txt = f" in {area}" if area else ""
    weather_txt = f" Weather conditions: {weather.lower()}." if weather else ""
    medical_txt = " Medical emergencies have been reported among those affected." if medical_emergency else ""

    priority_phrases = {
        "CRITICAL": "critical, life-threatening",
        "HIGH": "high-severity",
        "MEDIUM": "moderate but developing",
        "LOW": "low-severity but monitored",
    }
    phrase = priority_phrases.get(priority, "developing")

    return (
        f"{emergency} conditions{area_txt} are assessed as {phrase}, "
        f"with an estimated {people} people at risk.{medical_txt}{weather_txt}"
    ).strip()


def _recommendations(
    emergency: str,
    priority: str,
    medical_emergency: bool,
    people: int,
) -> List[str]:
    recs: List[str] = []
    emergency_lower = emergency.lower()

    if priority == "CRITICAL":
        recs.append("Dispatch the nearest available rescue team immediately")
    elif priority == "HIGH":
        recs.append("Prioritize rescue team assignment within the next response cycle")
    elif priority == "MEDIUM":
        recs.append("Schedule a rescue team visit and continue monitoring the situation")
    else:
        recs.append("Continue monitoring; no immediate team dispatch required")

    if "flood" in emergency_lower:
        recs.append("Deploy water rescue assets (boats, flotation equipment) to the affected area")
    if "fire" in emergency_lower:
        recs.append("Coordinate with fire suppression teams and establish a safety perimeter")
    if "earthquake" in emergency_lower or "collapse" in emergency_lower:
        recs.append("Deploy structural assessment and search-and-rescue teams")
    if "landslide" in emergency_lower:
        recs.append("Evacuate downslope structures and restrict access to the unstable area")

    if medical_emergency:
        recs.append("Request medical assistance and prepare triage supplies on-site")

    if people >= 200:
        recs.append("Consider large-scale evacuation and open a nearby shelter")
    elif people >= 50:
        recs.append("Prepare a local shelter option in case evacuation becomes necessary")

    recs.append("Keep affected residents informed via the citizen SOS channel")

    # Dedup while preserving order
    seen = set()
    unique = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique[:6]


def _potential_risks(priority: str, medical_emergency: bool, emergency: str) -> List[str]:
    risks = []
    emergency_lower = emergency.lower()

    if priority in ("CRITICAL", "HIGH"):
        risks.append("Situation may escalate faster than current response capacity")
    if "flood" in emergency_lower:
        risks.append("Rising water levels could cut off access routes")
    if "fire" in emergency_lower:
        risks.append("Fire spread risk to adjacent structures")
    if medical_emergency:
        risks.append("Delayed medical response could worsen patient outcomes")
    risks.append("Communication with affected residents may be intermittent")
    return risks[:4]


def _required_resources(emergency: str, medical_emergency: bool, people: int) -> List[str]:
    emergency_lower = emergency.lower()
    resources = []

    if "flood" in emergency_lower:
        resources.extend(["Rescue boats", "Life jackets", "Water pumps"])
    elif "fire" in emergency_lower:
        resources.extend(["Fire suppression units", "Protective gear"])
    elif "earthquake" in emergency_lower or "collapse" in emergency_lower:
        resources.extend(["Search-and-rescue equipment", "Structural shoring supplies"])
    else:
        resources.extend(["Rescue vehicles", "Emergency supplies"])

    if medical_emergency:
        resources.append("Medical kits")
        resources.append("Ambulance support")

    if people >= 100:
        resources.append("Temporary shelter capacity")

    resources.append("Communication equipment")

    seen = set()
    unique = []
    for r in resources:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique[:6]


def _confidence(priority: str, has_weather: bool, has_area: bool) -> float:
    base = {
        "CRITICAL": 0.90,
        "HIGH": 0.86,
        "MEDIUM": 0.80,
        "LOW": 0.75,
    }.get(priority, 0.75)
    if has_weather:
        base += 0.02
    if has_area:
        base += 0.02
    return round(min(base, 0.97), 2)


def analyze_incident(
    emergency: str,
    people: int,
    medical_emergency: bool,
    risk_score: int,
    priority: str,
    weather: Optional[str] = None,
    area: Optional[str] = None,
) -> Dict:
    """Core AI decision-support call. Deterministic fallback engine.

    This function is safe to call with no external API key — it IS the
    primary engine for the hackathon demo, not just a degraded path.
    """
    situation = _situation_summary(emergency, people, medical_emergency, priority, weather, area)
    recommendations = _recommendations(emergency, priority, medical_emergency, people)
    risks = _potential_risks(priority, medical_emergency, emergency)
    resources = _required_resources(emergency, medical_emergency, people)
    confidence = _confidence(priority, bool(weather), bool(area))

    return {
        "success": True,
        "situation": situation,
        "recommendations": recommendations,
        "potential_risks": risks,
        "required_resources": resources,
        "confidence": confidence,
        "advisory_notice": ADVISORY_NOTICE,
    }


def build_response_plan(
    zone_name: str,
    zone_id: str,
    risk_score: int,
    priority: str,
    people_at_risk: int,
    zone_status: str,
) -> Dict:
    """Generates a full response plan for a zone (used by 'Generate full
    response plan' button)."""
    situation = (
        f"{zone_name} is currently assessed at {priority} priority with a risk "
        f"score of {risk_score}/100. An estimated {people_at_risk} people are "
        f"at risk. Current zone status: {zone_status}."
    )

    recommended_actions = [
        f"Deploy the nearest available rescue team to {zone_name}",
        "Establish a triage and coordination point at the zone perimeter",
        "Open communication with residents via the citizen SOS channel",
        "Continuously reassess risk as conditions change",
    ]
    if priority == "CRITICAL":
        recommended_actions.insert(1, "Begin immediate evacuation of highest-risk structures")

    recommended_teams = ["Water Rescue Team", "Medical Team"]
    if priority in ("CRITICAL", "HIGH"):
        recommended_teams.append("Search & Rescue Team")

    resources = ["Rescue boats", "Medical kits", "Emergency supplies", "Communication equipment"]

    evacuation = (
        [
            "Prioritize evacuation of elderly, injured, and mobility-limited residents",
            "Identify and stage transport for at least the reported at-risk population",
            "Open the nearest designated shelter",
        ]
        if priority in ("CRITICAL", "HIGH")
        else [
            "Maintain evacuation readiness; formal evacuation not yet recommended",
        ]
    )

    medical = [
        "Stage medical personnel near the zone entry point",
        "Prepare for triage of injuries related to the emergency type",
    ]

    return {
        "zone": zone_name,
        "zone_id": zone_id,
        "risk_score": risk_score,
        "priority": priority,
        "situation": situation,
        "recommended_actions": recommended_actions,
        "recommended_teams": recommended_teams,
        "resources": resources,
        "evacuation_considerations": evacuation,
        "medical_considerations": medical,
        "advisory_notice": ADVISORY_NOTICE,
    }
