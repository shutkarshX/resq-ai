from app import models
from app.auth import create_access_token, hash_password


def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def test_public_sos_and_tracking_are_available_without_login(client):
    response = client.post("/api/reports", json={
        "emergency": "Flood", "people": 2, "medical_emergency": False,
        "flood_severity": 5, "infrastructure_damage": 0, "weather_severity": 5,
    })
    assert response.status_code == 201
    report_id = response.json()["report_id"]
    tracked = client.get(f"/api/public/reports/{report_id}")
    assert tracked.status_code == 200
    assert tracked.json()["status"] == "NEW"


def test_volunteer_cannot_access_commander_dashboard_or_operations(client, db_session):
    volunteer = models.User(name="Volunteer", email="v@test.local", password_hash=hash_password("password"), role="VOLUNTEER")
    db_session.add(volunteer)
    db_session.commit()
    headers = auth_headers(volunteer)
    assert client.get("/api/dashboard", headers=headers).status_code == 403
    assert client.get("/api/actions", headers=headers).status_code == 403
    assert client.get("/api/users", headers=headers).status_code == 403


def test_commander_can_view_users_and_derived_activity(client, db_session):
    commander = models.User(name="Commander", email="commander@users.test", password_hash=hash_password("password"), role="INCIDENT_COMMANDER")
    volunteer_user = models.User(name="Priya Sharma", email="priya@users.test", password_hash=hash_password("password"), role="VOLUNTEER")
    zone = models.RescueZone(id="Z-USERS", name="User Zone", latitude=23.2, longitude=77.4)
    db_session.add_all([commander, volunteer_user, zone])
    db_session.flush()
    volunteer = models.Volunteer(name="Priya Sharma", user_id=volunteer_user.id, skills="First Aid", location="User Zone")
    action = models.DispatchAction(zone_id=zone.id, action="Respond to Flood", status="IN_PROGRESS")
    db_session.add_all([volunteer, action])
    db_session.flush()
    db_session.add(models.VolunteerAssignment(
        volunteer_user_id=volunteer_user.id,
        action_id=action.id,
        instructions="Report to staging.",
        status="ASSIGNED",
    ))
    db_session.commit()

    response = client.get("/api/users", headers=auth_headers(commander))
    assert response.status_code == 200
    data = response.json()
    priya = next(user for user in data["users"] if user["email"] == "priya@users.test")
    assert priya["volunteer_location"] == "User Zone"
    assert priya["assignment_count"] == 1
    assert priya["active_assignment_count"] == 1
    assert priya["current_assignment"] == "Respond to Flood"
    assert any(event["label"] == "Priya Sharma assigned to Respond to Flood" for event in data["activity"])


def test_users_endpoint_requires_authentication(client):
    assert client.get("/api/users").status_code == 401


def test_removed_legacy_role_cannot_be_registered(client):
    response = client.post("/api/auth/register", json={"name": "Old role", "email": "old@test.local", "password": "password", "role": "LEGACY_OPERATOR"})
    assert response.status_code == 422
