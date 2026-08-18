def test_create_and_list_volunteer(seeded_client):
    resp = seeded_client.post("/api/volunteers", json={
        "name": "Test Volunteer", "skills": "First Aid", "location": "Zone A",
    })
    assert resp.status_code == 201
    vol_id = resp.json()["id"]

    listed = seeded_client.get("/api/volunteers").json()
    assert any(v["id"] == vol_id for v in listed)


def test_update_volunteer_status(seeded_client):
    create_resp = seeded_client.post("/api/volunteers", json={"name": "Test Volunteer"})
    vol_id = create_resp.json()["id"]

    resp = seeded_client.patch(f"/api/volunteers/{vol_id}", json={"status": "ASSIGNED"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ASSIGNED"


def test_update_unknown_volunteer_404(seeded_client):
    resp = seeded_client.patch("/api/volunteers/VOL-DOESNOTEXIST", json={"status": "OFFLINE"})
    assert resp.status_code == 404


def test_search_finds_zone(seeded_client):
    resp = seeded_client.get("/api/search?q=Riverside")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["zones"]) == 1
    assert data["zones"][0]["name"] == "Riverside Colony"


def test_search_finds_team(seeded_client):
    resp = seeded_client.get("/api/search?q=Water Rescue")
    assert resp.status_code == 200
    assert len(resp.json()["teams"]) == 1


def test_search_no_matches_returns_empty_lists(seeded_client):
    resp = seeded_client.get("/api/search?q=NoSuchThingExists")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zones"] == []
    assert data["incidents"] == []
