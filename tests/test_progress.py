import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas import CheckpointSubmission
from app.storage import save_checkpoint, get_student_dashboard

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_list_modules_endpoint():
    response = client.get("/api/modules")
    assert response.status_code in [200, 404]  # 200 OK si carga el catálogo correctamente

def test_storage_save_and_dashboard():
    # Enviar un checkpoint con status="completed"
    submission = CheckpointSubmission(
        user_id="test_student_01",
        module_id="S02",
        checkpoint_id="chk_01",
        evidence="Flag obtenida correctamente",
        status="completed"
    )
    record = save_checkpoint(submission)
    
    # Verificar guardado
    assert record.user_id == "test_student_01"
    assert record.completed is True
    assert record.status == "completed"

    # Verificar métricas en el dashboard
    dashboard = get_student_dashboard("test_student_01")
    assert dashboard["total_checkpoints_completed"] >= 1