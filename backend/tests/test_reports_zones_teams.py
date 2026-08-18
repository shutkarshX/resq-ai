def test_create_report_critical(seeded_client):
    payload = {
        "emergency": "Flood",
        "people": 500,
        "medical_emergency": True,
        "location": "23.26,77.41",
        "latitude": 23.2599,
        "longitude": 77.4126,
        "flood_severity": 25,
        "infrastructure_damage": 15,
        "weather_severity": 10,
    }
    resp = seeded_client.post("/api/reports", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["accepted"] is True
    assert data["priority"] == "CRITICAL"
    assert data["risk_score"] == 100
    assert data["zone_id"] == "Z-01"  # nearest zone to given coords


def test_get_reports_filter_by_priority(seeded_client):
    seeded_client.post("/api/reports", json={
        "emergency": "Flood", "people": 500, "medical_emergency": True,
        "latitude": 23.2599, "longitude": 77.4126,
        "flood_severity": 25, "infrastructure_damage": 15, "weather_severity": 10,
    })
    seeded_client.post("/api/reports", json={
        "emergency": "Minor leak", "people": 1, "medical_emergency": False,
        "latitude": 23.2599, "longitude": 77.4126,
        "flood_severity": 0, "infrastructure_damage": 0, "weather_severity": 0,
    })

    resp = seeded_client.get("/api/reports?priority=CRITICAL")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["priority"] == "CRITICAL"


def test_list_zones(seeded_client):
    resp = seeded_client.get("/api/zones")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "Z-01"


def test_get_zone_404(seeded_client):
    resp = seeded_client.get("/api/zones/Z-99")
    assert resp.status_code == 404


def test_list_teams_and_available(seeded_client):
    resp = seeded_client.get("/api/teams")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp2 = seeded_client.get("/api/teams/available")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1
