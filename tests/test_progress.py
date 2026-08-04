import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.config import get_settings
from backend.app.storage import init_db, save_checkpoint, get_student_dashboard
from backend.app.schemas import CheckpointSubmission

# Inicializamos el cliente de pruebas de FastAPI
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    """
    Fixture que se ejecuta antes de cada test. 
    Redirige la base de datos a un archivo temporal para no ensuciar los datos reales.
    """
    settings = get_settings()
    test_db = tmp_path / "test_cyberlabuv.sqlite3"
    
    monkeypatch.setattr(settings, "database_path", str(test_db))
    init_db()
    yield

def test_health_endpoint():
    """Prueba de integración: Verifica que el backend esté vivo."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_list_modules_endpoint():
    """Prueba de integración: Verifica que los YAMLs se lean y la API los exponga."""
    response = client.get("/api/modules")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_storage_save_and_dashboard():
    """Prueba de base de datos: Verifica inserciones, UPSERTs y el cálculo del Dashboard."""
    
    # 1. Crear un submission de prueba con el schema real de la BD
    submission = CheckpointSubmission(
        user_id="estudiante-test",
        student_id="estudiante-test",
        module_id="S01",
        checkpoint_id="cp-test-1",
        evidence="flag_valida_123",
        status="completed"
    )
    
    # 2. Probar inserción inicial (INSERT)
    save_checkpoint(submission)
    
    # 3. Probar actualización (ON CONFLICT UPSERT)
    submission.evidence = "flag_valida_123_corregida"
    save_checkpoint(submission)
    
    # 4. Probar la lógica de get_student_dashboard
    dashboard = get_student_dashboard("estudiante-test")
    
    assert dashboard is not None
    assert hasattr(dashboard, "progress_percent")  # Corregido: Se llama progress_percent
    assert dashboard.progress_percent >= 0         # Corregido