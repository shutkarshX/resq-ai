def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "resq-ai"
    assert data["database"] == "connected"


def test_dashboard_empty_db_returns_zeros(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["metrics"]["active_incidents"] == 0
    assert data["metrics"]["people_at_risk"] == 0
    assert data["metrics"]["teams_total"] == 0
    assert data["zones"] == []


def test_dashboard_reflects_seeded_data(seeded_client):
    resp = seeded_client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["zones"]) == 1
    assert data["zones"][0]["id"] == "Z-01"
    assert data["metrics"]["teams_total"] == 1


def test_dashboard_updates_after_sos(seeded_client):
    before = seeded_client.get("/api/dashboard").json()
    assert before["metrics"]["active_incidents"] == 0

    payload = {
        "emergency": "Flood",
        "people": 35,
        "medical_emergency": True,
        "location": "23.26,77.41",
        "latitude": 23.26,
        "longitude": 77.41,
        "flood_severity": 25,
        "infrastructure_damage": 7,
        "weather_severity": 10,
    }
    r = seeded_client.post("/api/reports", json=payload)
    assert r.status_code == 201

    after = seeded_client.get("/api/dashboard").json()
    assert after["metrics"]["active_incidents"] == 1
    assert after["metrics"]["people_at_risk"] == 35
