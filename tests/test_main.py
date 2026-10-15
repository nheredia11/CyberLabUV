from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_session

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_storage_save_and_dashboard():
    # Crear token válido para el estudiante de prueba
    token = create_session("test_student_1", "student", "student@uv.edu.co")
    headers = {"Authorization": f"Bearer {token}"}

    # Verifica catálogo (público)
    res_catalog = client.get("/api/modules")
    assert res_catalog.status_code == 200
    
    # Verifica dashboard con token de autorización
    res_dash = client.get("/api/students/test_student_1/dashboard", headers=headers)
    assert res_dash.status_code == 200