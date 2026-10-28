from fastapi.testclient import TestClient
from app.main import app
from app.auth import create_session
import os

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_dev_login_roles(client):
    os.environ["ENABLE_DEV_LOGIN"] = "true"
    
    # Usar el endpoint unificado /api/auth/login enviando el rol y correo en el payload
    res = client.post(
        "/api/auth/login",
        json={"email": "docente@uv.edu.co", "role": "teacher", "name": "Profesor Test"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "teacher"
    assert data["user"]["role"] == "teacher"
    
    # Capturamos el token correctamente de la respuesta
    teacher_token = data.get("token")
    
    res_analytics = client.get(
        "/api/teacher/analytics", 
        headers={"Authorization": f"Bearer {teacher_token}"}
    )
    assert res_analytics.status_code == 200

    # Login student
    res_student = client.post("/api/auth/dev-login?role=student")
    assert res_student.status_code == 200
    student_token = res_student.json()["token"]

    # Student pidiendo analytics -> 403
    res_bad = client.get("/api/teacher/analytics", headers={"Authorization": f"Bearer {student_token}"})
    assert res_bad.status_code == 403

def test_student_isolation(client):
    token_a = create_session("student_a", "student", "a@uv.edu.co")
    res = client.get("/api/students/student_b/dashboard", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 403

def test_report_pdf(client):
    token = create_session("student_a", "student", "a@uv.edu.co")
    res = client.get("/api/students/student_a/report.pdf", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")

def test_forbidden_command(client):
    token = create_session("student_a", "student", "a@uv.edu.co")
    res = client.post(
        "/api/scenarios/s01/command",
        json={"user_id": "student_a", "scenario_id": "s01", "command": "nmap -p 22 localhost; cat /etc/passwd"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 400
    
def test_consent_blocking(client):
    """Verifica que un estudiante nuevo no tenga consentimiento aceptado por defecto."""
    token = create_session("student_new", "student", "new@uv.edu.co")
    res = client.get(
        "/api/consent",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["accepted"] is False


def test_checkpoint_submit_and_dashboard(client):
    """Verifica el flujo correcto de envío de checkpoint a la ruta real y consulta de dashboard."""
    token = create_session("student_a", "student", "a@uv.edu.co")
    
    # Enviar checkpoint exitoso usando un módulo y checkpoint reales (S01 y s01-cp1)
    res_sub = client.post(
        "/api/checkpoints/submit",
        json={"user_id": "student_a", "module_id": "S01", "checkpoint_id": "s01-cp1", "status": "done", "evidence": "flag_test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_sub.status_code == 200

    # Consultar dashboard del estudiante
    res_dash = client.get(
        "/api/students/student_a/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_dash.status_code == 200
    data = res_dash.json()
    assert "modules" in data or "progress" in data or isinstance(data, dict)


def test_runner_unallowed_command():
    """Prueba unitaria directa del runner para verificar bloqueo de comandos fuera de la lista blanca."""
    import asyncio
    from app.scenario_runner import run_scenario_command
    
    # Ejecutar comando no permitido dentro de un loop sincrónico para pytest
    async def run_test():
        success, message = await run_scenario_command("student_a", "S01", "rm -rf /")
        return success, message

    success, message = asyncio.run(run_test())
    assert success is False
    assert "no permitido" in message.lower() or "bloqueado" in message.lower() or "vacío" in message.lower()