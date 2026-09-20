import io
from fastapi.testclient import TestClient
from app.main import app
from app.services.explanation_service import explanation_service

client = TestClient(app)


def create_dummy_image():
    # 10x10 RGB dummy image bytes (JPEG format header/bytes simulated or simple dummy PNG)
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x02\x00\x00\x00\x02"
        b"\x8d\xb1\xb2\x00\x00\x00\x0cIDATx\x9cc` \x05\x08\x00\x00\x00\xff\xff\x03\x00\x05\x00\x01"
        b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def create_dummy_wav():
    # 44-byte minimal WAV header
    return (
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00"
        b"\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )


def test_single_modality_environment():
    response = client.post(
        "/analyze/environment",
        data={"temperature": 34.0, "humidity": 75.0}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["temperature"] == 34.0
    assert data["humidity"] == 75.0
    assert data["risk_score"] > 60
    assert any(ind in ["potential_heat_stress_environment", "extreme_heat_risk_environment"] for ind in data["indicators"])



def test_multimodal_image_and_environment():
    img_bytes = create_dummy_image()
    files = {"image": ("test.png", io.BytesIO(img_bytes), "image/png")}
    data = {
        "animal_id": "Cow-Test-ImageEnv",
        "species": "cattle",
        "age": 4.0,
        "temperature": 35.0,
        "humidity": 78.0
    }
    response = client.post("/analyze", data=data, files=files)
    assert response.status_code == 200
    res = response.json()

    # Schema verification
    assert "analysis_id" in res
    assert res["animal"]["animal_id"] == "Cow-Test-ImageEnv"
    assert res["risk"]["level"] in ["ATTENTION", "HIGH_RISK"]
    assert "image" in res["modalities_analyzed"]
    assert "environment" in res["modalities_analyzed"]
    assert len(res["indicators"]) > 0

    # Indicator structure check
    for ind in res["indicators"]:
        assert "modality" in ind
        assert "name" in ind
        assert "confidence" in ind
        assert "description" in ind

    # Exact recommendation check
    assert res["recommendation"] == explanation_service.EXACT_RECOMMENDATION
    assert res["alert_created"] is True
    assert res["alert"] is not None


def test_multimodal_image_and_audio():
    img_bytes = create_dummy_image()
    wav_bytes = create_dummy_wav()
    files = {
        "image": ("test.png", io.BytesIO(img_bytes), "image/png"),
        "audio": ("test.wav", io.BytesIO(wav_bytes), "audio/wav")
    }
    data = {
        "animal_id": "Goat-Test-ImgAud",
        "species": "goat"
    }
    response = client.post("/analyze", data=data, files=files)
    assert response.status_code == 200
    res = response.json()

    assert "image" in res["modalities_analyzed"]
    assert "audio" in res["modalities_analyzed"]
    assert "environment" not in res["modalities_analyzed"]


def test_missing_all_modalities_error():
    data = {
        "animal_id": "Cow-Err",
        "species": "cattle"
    }
    response = client.post("/analyze", data=data)
    assert response.status_code == 400
    assert "At least one modality" in response.json()["message"]
