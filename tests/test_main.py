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