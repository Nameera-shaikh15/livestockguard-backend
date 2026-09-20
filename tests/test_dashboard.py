from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_and_demo_endpoints():
    # 1. Access Demo endpoint for Cow-17
    demo_res = client.get("/demo/analysis/Cow-17")
    assert demo_res.status_code == 200
    demo_data = demo_res.json()

    assert demo_data["animal"]["animal_id"] == "Cow-17"
    assert demo_data["risk"]["level"] == "HIGH_RISK"
    assert demo_data["risk"]["score"] == 78
    assert demo_data["alert_created"] is True
    assert demo_data["alert"]["status"] == "ACTIVE"

    # 2. Access Dashboard summary
    dash_res = client.get("/dashboard/summary")
    assert dash_res.status_code == 200
    summary = dash_res.json()

    assert "total_animals" in summary
    assert "normal" in summary
    assert "attention" in summary
    assert "high_risk" in summary
    assert "resolved_alerts" in summary
    assert "recent_alerts" in summary

    assert summary["total_animals"] > 0
    assert summary["high_risk"] >= 1


def test_demo_resolved_buffalo():
    demo_res = client.get("/demo/analysis/Buffalo-02")
    assert demo_res.status_code == 200
    demo_data = demo_res.json()
    assert demo_data["animal"]["animal_id"] == "Buffalo-02"
    assert demo_data["alert"]["status"] == "RESOLVED"
