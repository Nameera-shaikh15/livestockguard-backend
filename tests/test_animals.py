from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_get_animal():
    payload = {
        "animal_id": "Cow-Test-01",
        "species": "cattle",
        "age": 3.5,
        "farm_id": "Farm-Test"
    }
    response = client.post("/animals", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["animal_id"] == "Cow-Test-01"
    assert data["species"] == "cattle"
    assert data["current_status"] == "NORMAL"

    # Get animal detail
    get_res = client.get("/animals/Cow-Test-01")
    assert get_res.status_code == 200
    assert get_res.json()["animal_id"] == "Cow-Test-01"

    # List animals
    list_res = client.get("/animals")
    assert list_res.status_code == 200
    assert any(a["animal_id"] == "Cow-Test-01" for a in list_res.json())
