import os


def test_ai_analyze_fallback_works_without_api_key(seeded_client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    resp = seeded_client.post("/api/ai/analyze", json={
        "emergency": "Flood",
        "people": 35,
        "medical_emergency": True,
        "weather": "Heavy rainfall",
        "area": "Residential area",
        "risk_score": 92,
        "priority": "CRITICAL",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["recommendations"]) > 0
    assert "advisory" in data["advisory_notice"].lower() or "human operator" in data["advisory_notice"].lower()
    assert 0 <= data["confidence"] <= 1


def test_ai_analyze_never_claims_real_dispatch(seeded_client):
    resp = seeded_client.post("/api/ai/analyze", json={
        "emergency": "Flood", "people": 500, "medical_emergency": True,
        "risk_score": 100, "priority": "CRITICAL",
    })
    data = resp.json()
    full_text = " ".join(data["recommendations"]).lower() + data["situation"].lower()
    # The AI must never claim it HAS dispatched/contacted/evacuated (past tense claims).
    forbidden_phrases = ["has been dispatched", "has contacted", "has evacuated", "police have been notified"]
    for phrase in forbidden_phrases:
        assert phrase not in full_text


def test_ai_analyze_with_incident_uses_stored_risk(seeded_client):
    report_resp = seeded_client.post("/api/reports", json={
        "emergency": "Flood", "people": 500, "medical_emergency": True,
        "latitude": 23.2599, "longitude": 77.4126,
        "flood_severity": 25, "infrastructure_damage": 15, "weather_severity": 10,
    })
    incident_id = report_resp.json()["incident_id"]

    resp = seeded_client.post("/api/ai/analyze", json={
        "incident_id": incident_id,
        "emergency": "Flood",
        "people": 500,
        "medical_emergency": True,
    })
    assert resp.status_code == 200
    assert resp.json()["confidence"] > 0.85  # CRITICAL priority -> high confidence


def test_ai_analyze_unknown_incident_404(seeded_client):
    resp = seeded_client.post("/api/ai/analyze", json={
        "incident_id": "INC-DOESNOTEXIST",
        "emergency": "Flood",
        "people": 10,
    })
    assert resp.status_code == 404


def test_response_plan_for_zone(seeded_client):
    resp = seeded_client.post("/api/ai/response-plan", json={"zone_id": "Z-01"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone"] == "Riverside Colony"
    assert data["priority"] == "CRITICAL"  # risk_score 96 seeded
    assert len(data["recommended_actions"]) > 0
    assert len(data["recommended_teams"]) > 0


def test_response_plan_unknown_zone_404(seeded_client):
    resp = seeded_client.post("/api/ai/response-plan", json={"zone_id": "Z-99"})
    assert resp.status_code == 404


def test_dashboard_ai_summary_updates_after_analysis(seeded_client):
    seeded_client.post("/api/ai/analyze", json={
        "emergency": "Flood", "people": 500, "medical_emergency": True,
        "risk_score": 100, "priority": "CRITICAL",
    })
    dashboard = seeded_client.get("/api/dashboard").json()
    assert "flood" in dashboard["ai_summary"].lower() or "500" in dashboard["ai_summary"]
