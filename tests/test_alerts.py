from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_alert_creation_and_resolution_flow():
    # 1. Trigger analysis that generates HIGH_RISK alert
    data = {
        "animal_id": "Cow-Alert-Test",
        "species": "cattle",
        "temperature": 36.0,
        "humidity": 82.0
    }
    analyze_res = client.post("/analyze", data=data)
    assert analyze_res.status_code == 200
    res = analyze_res.json()

    assert res["alert_created"] is True
    alert_info = res["alert"]
    alert_id = alert_info["alert_id"]
    assert alert_info["status"] == "ACTIVE"

    # Verify animal status is updated to HIGH_RISK or ATTENTION
    animal_res = client.get("/animals/Cow-Alert-Test")
    assert animal_res.status_code == 200
    assert animal_res.json()["current_status"] in ["HIGH_RISK", "ATTENTION"]

    # 2. Check active alerts list
    active_res = client.get("/alerts/active")
    assert active_res.status_code == 200
    active_ids = [a["alert_id"] for a in active_res.json()]
    assert alert_id in active_ids

    # 3. Resolve the alert
    resolve_res = client.post(f"/alerts/{alert_id}/resolve")
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["alert"]["status"] == "RESOLVED"
    assert res_data["alert"]["resolved_at"] is not None

    # 4. Verify active list no longer has alert, resolved list does
    active_res_2 = client.get("/alerts/active")
    active_ids_2 = [a["alert_id"] for a in active_res_2.json()]
    assert alert_id not in active_ids_2

    resolved_res = client.get("/alerts/resolved")
    resolved_ids = [a["alert_id"] for a in resolved_res.json()]
    assert alert_id in resolved_ids

    # 5. Verify animal's current status returned to NORMAL
    animal_res_after = client.get("/animals/Cow-Alert-Test")
    assert animal_res_after.json()["current_status"] == "NORMAL"
