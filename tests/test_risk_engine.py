from app.services.risk_engine import risk_engine


def test_risk_engine_all_modalities():
    res = risk_engine.calculate_risk(
        visual_score=80.0,
        behaviour_score=90.0,
        audio_score=70.0,
        environment_score=80.0
    )
    assert res["risk_score"] >= 65
    assert res["risk_level"] == "HIGH_RISK"
    assert set(res["modalities_analyzed"]) == {"image", "video", "audio", "environment"}


def test_risk_engine_missing_modalities():
    # Test image + environment only (Visual 0.25, Environment 0.25 -> total 0.50)
    # Visual: 80, Environment: 80 -> Composite should be 80
    res = risk_engine.calculate_risk(
        visual_score=80.0,
        environment_score=80.0
    )
    assert res["risk_score"] == 80
    assert res["risk_level"] == "HIGH_RISK"
    assert set(res["modalities_analyzed"]) == {"image", "environment"}
    assert "audio" not in res["modalities_analyzed"]
    assert "video" not in res["modalities_analyzed"]


def test_risk_engine_normal_level():
    res = risk_engine.calculate_risk(
        visual_score=10.0,
        behaviour_score=15.0
    )
    assert res["risk_score"] < 35
    assert res["risk_level"] == "NORMAL"


def test_risk_engine_attention_level():
    res = risk_engine.calculate_risk(
        visual_score=50.0,
        behaviour_score=45.0
    )
    assert 35 <= res["risk_score"] < 65
    assert res["risk_level"] == "ATTENTION"
