from app.risk_engine import calculate_risk


def test_low_risk():
    result = calculate_risk(
        people=5, flood_severity=0, medical_emergency=False,
        infrastructure_damage=0, weather_severity=0,
    )
    assert result["priority"] == "LOW"
    assert result["risk_score"] <= 30


def test_critical_risk():
    result = calculate_risk(
        people=500, flood_severity=25, medical_emergency=True,
        infrastructure_damage=15, weather_severity=10,
    )
    assert result["risk_score"] == 100
    assert result["priority"] == "CRITICAL"


def test_medical_emergency_adds_20_points():
    without_medical = calculate_risk(
        people=0, flood_severity=0, medical_emergency=False,
        infrastructure_damage=0, weather_severity=0,
    )
    with_medical = calculate_risk(
        people=0, flood_severity=0, medical_emergency=True,
        infrastructure_damage=0, weather_severity=0,
    )
    assert with_medical["risk_score"] - without_medical["risk_score"] == 20


def test_score_never_exceeds_100():
    result = calculate_risk(
        people=999999, flood_severity=999, medical_emergency=True,
        infrastructure_damage=999, weather_severity=999,
    )
    assert result["risk_score"] == 100


def test_breakdown_sums_to_total():
    result = calculate_risk(
        people=100, flood_severity=15, medical_emergency=True,
        infrastructure_damage=8, weather_severity=6,
    )
    breakdown_sum = sum(result["breakdown"].values())
    assert breakdown_sum == result["risk_score"]


def test_priority_boundaries():
    assert calculate_risk(0, 0, False, 0, 0)["priority"] == "LOW"          # 0
    assert calculate_risk(0, 25, False, 15, 0)["priority"] == "MEDIUM"     # 40
    assert calculate_risk(0, 25, True, 15, 10)["priority"] == "HIGH"       # 70
    assert calculate_risk(500, 25, True, 15, 10)["priority"] == "CRITICAL"  # 100
