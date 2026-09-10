from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_storage_save_and_dashboard():
    # Verifica catálogo
    res_catalog = client.get("/api/modules")
    assert res_catalog.status_code == 200

    # Verifica dashboard inicial
    res_dash = client.get("/api/students/test_student_1/dashboard")
    assert res_dash.status_code == 200
    data = res_dash.json()
    assert data["student_id"] == "test_student_1"