"""Seed the database with realistic, internally-consistent demo data.

Run with:  python seed.py

Safe to re-run: it clears existing rows first, so you always get a clean,
deterministic demo state (no random values).
"""
import logging
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal, init_db, engine, Base
from app import models
from app.risk_engine import calculate_risk, priority_color

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("resq-ai.seed")

BHOPAL_ZONES = [
    # Matches the frontend's hardcoded zones/coords exactly.
    {"id": "Z-01", "name": "Riverside Colony", "lat": 23.2599, "lon": 77.4126,
     "risk_score": 96, "people_at_risk": 420, "status": "Immediate evacuation", "color": "#ff5f5f"},
    {"id": "Z-02", "name": "Old Market Ward", "lat": 23.2638, "lon": 77.4012,
     "risk_score": 81, "people_at_risk": 185, "status": "Rescue in progress", "color": "#ffb547"},
    {"id": "Z-03", "name": "Shanti Nagar", "lat": 23.2471, "lon": 77.4168,
     "risk_score": 68, "people_at_risk": 96, "status": "Shelter activated", "color": "#ffd166"},
]

TEAMS = [
    {"id": "TEAM-01", "name": "Alpha Water Rescue", "team_type": "Water Rescue", "members": 6},
    {"id": "TEAM-02", "name": "Bravo Medical Unit", "team_type": "Medical", "members": 4},
    {"id": "TEAM-03", "name": "Charlie Search & Rescue", "team_type": "Search & Rescue", "members": 8},
    {"id": "TEAM-04", "name": "Delta Water Rescue", "team_type": "Water Rescue", "members": 6},
    {"id": "TEAM-05", "name": "Echo Logistics", "team_type": "Logistics & Supplies", "members": 5},
    {"id": "TEAM-06", "name": "Foxtrot Medical Unit", "team_type": "Medical", "members": 4},
]

VOLUNTEERS = [
    {"name": "Priya Sharma", "skills": "First Aid, Swimming", "location": "Riverside Colony"},
    {"name": "Rohit Verma", "skills": "Logistics, Driving", "location": "Old Market Ward"},
    {"name": "Anita Desai", "skills": "Medical, Triage", "location": "Shanti Nagar"},
    {"name": "Karan Mehta", "skills": "Communications", "location": "Bhopal Central"},
    {"name": "Sneha Iyer", "skills": "First Aid, Cooking", "location": "Riverside Colony"},
]


def clear_all(db):
    # Delete in FK-safe order.
    db.query(models.AIAnalysis).delete()
    db.query(models.DispatchAction).delete()
    db.query(models.SOSReport).delete()
    db.query(models.Incident).delete()
    db.query(models.Volunteer).delete()
    db.query(models.RescueTeam).delete()
    db.query(models.RescueZone).delete()
    db.commit()


def seed():
    init_db()
    db = SessionLocal()
    try:
        logger.info("Clearing existing data...")
        clear_all(db)

        logger.info("Seeding zones...")
        zone_objs = {}
        for z in BHOPAL_ZONES:
            zone = models.RescueZone(
                id=z["id"], name=z["name"], latitude=z["lat"], longitude=z["lon"],
                risk_score=z["risk_score"], people_at_risk=z["people_at_risk"],
                status=z["status"], color=z["color"],
            )
            db.add(zone)
            zone_objs[z["id"]] = zone
        db.flush()

        logger.info("Seeding rescue teams...")
        team_objs = {}
        for t in TEAMS:
            team = models.RescueTeam(
                id=t["id"], name=t["name"], team_type=t["team_type"],
                members=t["members"], status="AVAILABLE",
            )
            db.add(team)
            team_objs[t["id"]] = team
        db.flush()

        logger.info("Seeding volunteers...")
        for v in VOLUNTEERS:
            db.add(models.Volunteer(
                name=v["name"], skills=v["skills"], location=v["location"],
                availability="AVAILABLE", status="AVAILABLE",
            ))

        logger.info("Seeding incidents (one per zone, matching zone risk)...")
        incident_objs = {}
        incident_defs = [
            ("Z-01", "Flood", "Riverside Colony flooding — eastern embankment breach", 420, True),
            ("Z-02", "Flood", "Old Market Ward road access threatened by rising water", 185, True),
            ("Z-03", "Flood", "Shanti Nagar low-lying homes affected, shelter active", 96, False),
        ]
        for zone_id, etype, desc, people, medical in incident_defs:
            zone = zone_objs[zone_id]
            risk = calculate_risk(
                people=people,
                flood_severity=25 if zone.risk_score > 90 else 20 if zone.risk_score > 75 else 15,
                medical_emergency=medical,
                infrastructure_damage=10 if zone.risk_score > 90 else 7 if zone.risk_score > 75 else 4,
                weather_severity=10 if zone.risk_score > 90 else 8 if zone.risk_score > 75 else 5,
            )
            incident = models.Incident(
                title=f"{etype} — {zone.name}",
                emergency_type=etype,
                description=desc,
                latitude=zone.latitude,
                longitude=zone.longitude,
                people_at_risk=people,
                medical_emergency=medical,
                risk_score=risk["risk_score"],
                priority=risk["priority"],
                status="ACTIVE",
                zone_id=zone_id,
            )
            db.add(incident)
            db.flush()
            incident_objs[zone_id] = incident

        # One additional resolved incident for historical/demo variety.
        resolved_incident = models.Incident(
            title="Flood — Old Market Ward (earlier wave)",
            emergency_type="Flood",
            description="Earlier flood wave, resolved after successful evacuation.",
            latitude=zone_objs["Z-02"].latitude,
            longitude=zone_objs["Z-02"].longitude,
            people_at_risk=60,
            medical_emergency=False,
            risk_score=55,
            priority="MEDIUM",
            status="RESOLVED",
            zone_id="Z-02",
            created_at=datetime.now(timezone.utc) - timedelta(hours=6),
            updated_at=datetime.now(timezone.utc) - timedelta(hours=4),
        )
        db.add(resolved_incident)

        db.flush()

        logger.info("Seeding SOS reports...")
        report_defs = [
            ("Z-01", "Flood", 40, True, "Elderly couple trapped on second floor", 25, 10, 10),
            ("Z-01", "Flood", 15, False, "Family stranded on rooftop", 25, 8, 10),
            ("Z-01", "Medical", 2, True, "Injury reported during evacuation attempt", 15, 5, 8),
            ("Z-01", "Flood", 60, True, "Apartment block cut off by rising water", 25, 12, 10),
            ("Z-02", "Flood", 20, False, "Road access blocked near market bridge", 18, 9, 7),
            ("Z-02", "Flood", 12, True, "Shop owners requesting evacuation assistance", 18, 6, 7),
            ("Z-02", "Infrastructure", 8, False, "Power lines down near market entrance", 10, 12, 6),
            ("Z-03", "Flood", 10, False, "Low-lying homes taking on water", 12, 4, 5),
            ("Z-03", "Shelter", 25, False, "Shelter requesting additional supplies", 8, 3, 4),
            ("Z-03", "Medical", 3, True, "Minor injuries at shelter site", 8, 3, 4),
        ]
        for i, (zone_id, etype, people, medical, summary, flood, infra, weather) in enumerate(report_defs):
            risk = calculate_risk(
                people=people, flood_severity=flood, medical_emergency=medical,
                infrastructure_damage=infra, weather_severity=weather,
            )
            report = models.SOSReport(
                emergency=etype,
                people=people,
                medical_emergency=medical,
                location=f"{zone_objs[zone_id].name} area",
                latitude=zone_objs[zone_id].latitude,
                longitude=zone_objs[zone_id].longitude,
                flood_severity=flood,
                infrastructure_damage=infra,
                weather_severity=weather,
                risk_score=risk["risk_score"],
                priority=risk["priority"],
                status="TRIAGED" if i % 3 == 0 else "NEW",
                zone_id=zone_id,
                incident_id=incident_objs[zone_id].id,
                source="Citizen SOS",
                summary=summary,
                created_at=datetime.now(timezone.utc) - timedelta(minutes=(len(report_defs) - i) * 12),
            )
            db.add(report)

        db.flush()

        logger.info("Seeding dispatch actions...")
        # Deploy a couple of teams already, complete one for historical data.
        team_objs["TEAM-01"].status = "DEPLOYED"
        team_objs["TEAM-01"].current_zone_id = "Z-01"
        team_objs["TEAM-02"].status = "DEPLOYED"
        team_objs["TEAM-02"].current_zone_id = "Z-01"
        db.add(team_objs["TEAM-01"])
        db.add(team_objs["TEAM-02"])

        db.add(models.DispatchAction(
            zone_id="Z-01", team_id="TEAM-01", action="Evacuate Riverside Colony",
            status="DEPLOYED",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=40),
        ))
        db.add(models.DispatchAction(
            zone_id="Z-01", team_id="TEAM-02", action="Prioritize medical extraction",
            status="DEPLOYED",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=25),
        ))
        db.add(models.DispatchAction(
            zone_id="Z-02", team_id="TEAM-04", action="Move supplies to Old Market Ward",
            status="COMPLETED",
            created_at=datetime.now(timezone.utc) - timedelta(hours=5),
            completed_at=datetime.now(timezone.utc) - timedelta(hours=4),
        ))
        db.add(models.DispatchAction(
            zone_id="Z-03", team_id=None, action="Restock Shanti Nagar shelter",
            status="QUEUED",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        ))
        db.add(models.DispatchAction(
            zone_id="Z-02", team_id="TEAM-06", action="Medical triage at market ward",
            status="IN_PROGRESS",
            created_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        ))
        team_objs["TEAM-06"].status = "DEPLOYED"
        team_objs["TEAM-06"].current_zone_id = "Z-02"
        db.add(team_objs["TEAM-06"])

        logger.info("Seeding one AI analysis (drives dashboard ai_summary)...")
        import json
        db.add(models.AIAnalysis(
            incident_id=incident_objs["Z-01"].id,
            situation_summary=(
                "Heavy rainfall has caused the Kolar River to breach its eastern bank. "
                "Three zones show compounding flood risk, with an estimated 701 people "
                "requiring support within the next 2 hours."
            ),
            recommendations=json.dumps([
                "Dispatch the nearest available rescue team immediately",
                "Deploy water rescue assets to the affected area",
                "Request medical assistance and prepare triage supplies on-site",
                "Consider large-scale evacuation and open a nearby shelter",
            ]),
            confidence=0.94,
        ))

        db.commit()
        logger.info("Seed complete.")

        # Summary printout
        print("\n--- Seed summary ---")
        print(f"Zones: {db.query(models.RescueZone).count()}")
        print(f"Teams: {db.query(models.RescueTeam).count()}")
        print(f"Incidents: {db.query(models.Incident).count()}")
        print(f"SOS reports: {db.query(models.SOSReport).count()}")
        print(f"Volunteers: {db.query(models.Volunteer).count()}")
        print(f"Dispatch actions: {db.query(models.DispatchAction).count()}")
        print(f"AI analyses: {db.query(models.AIAnalysis).count()}")
        print("--------------------\n")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
