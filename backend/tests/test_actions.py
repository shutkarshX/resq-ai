def test_assign_action_deploys_available_team(seeded_client):
    resp = seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01",
        "action": "Evacuate Riverside Colony",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["accepted"] is True
    assert data["team_id"] == "TEAM-01"
    assert data["status"] == "DEPLOYED"

    # Team should now show as DEPLOYED.
    team = seeded_client.get("/api/teams/TEAM-01").json()
    assert team["status"] == "DEPLOYED"
    assert team["current_zone_id"] == "Z-01"


def test_assign_action_unknown_zone_404(seeded_client):
    resp = seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-99",
        "action": "Do something",
    })
    assert resp.status_code == 404


def test_cannot_assign_unavailable_team(seeded_client):
    # First assignment deploys TEAM-01.
    seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01", "action": "First action",
    })
    # Explicitly requesting the now-deployed team should 409.
    resp = seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01", "action": "Second action", "team_id": "TEAM-01",
    })
    assert resp.status_code == 409


def test_assign_with_no_teams_available_queues_action(seeded_client):
    # Deploy the only team first.
    seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01", "action": "First action",
    })
    # Now no teams are available; a second assign (no team_id) should queue, not fail.
    resp = seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01", "action": "Second action",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["team_id"] is None
    assert data["status"] == "QUEUED"


def test_complete_action_frees_team_and_resolves_incident(seeded_client):
    # Create an incident via SOS so there's something to resolve.
    seeded_client.post("/api/reports", json={
        "emergency": "Flood", "people": 100, "medical_emergency": True,
        "latitude": 23.2599, "longitude": 77.4126,
        "flood_severity": 20, "infrastructure_damage": 10, "weather_severity": 8,
    })

    assign_resp = seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01", "action": "Evacuate Riverside Colony",
    })
    action_id = assign_resp.json()["action_id"]

    complete_resp = seeded_client.patch(f"/api/actions/{action_id}", json={"status": "COMPLETED"})
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "COMPLETED"
    assert complete_resp.json()["completed_at"] is not None

    team = seeded_client.get("/api/teams/TEAM-01").json()
    assert team["status"] == "AVAILABLE"
    assert team["current_zone_id"] is None


def test_dashboard_cases_resolved_increments(seeded_client):
    before = seeded_client.get("/api/dashboard").json()["metrics"]["cases_resolved"]

    assign_resp = seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01", "action": "Test action",
    })
    action_id = assign_resp.json()["action_id"]
    seeded_client.patch(f"/api/actions/{action_id}", json={"status": "COMPLETED"})

    after = seeded_client.get("/api/dashboard").json()["metrics"]["cases_resolved"]
    assert after == before + 1


def test_update_action_invalid_status_rejected(seeded_client):
    assign_resp = seeded_client.post("/api/actions/assign", json={
        "zone_id": "Z-01", "action": "Test action",
    })
    action_id = assign_resp.json()["action_id"]
    resp = seeded_client.patch(f"/api/actions/{action_id}", json={"status": "NOT_A_REAL_STATUS"})
    assert resp.status_code == 422
