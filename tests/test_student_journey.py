"""Recorrido completo de un estudiante, de punta a punta (con Docker simulado).

Es la prueba que detecta los desajustes entre lo que calcula el backend y lo que muestra la interfaz.
"""
import json
import pathlib
import re

import app.scenario_runner as r
from app.schemas import DashboardModule, ModuleProgressView, StudentDashboard

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "frontend" / "src" / "pages"


def _login(client, role="student", email="estudiante@uv.edu.co"):
    res = client.post("/api/auth/login", json={"email": email, "role": role})
    assert res.status_code == 200, res.text
    body = res.json()
    return {"Authorization": f"Bearer {body['token']}"}, body["user_id"]


def test_student_full_journey(client, monkeypatch):
    monkeypatch.setattr(r.settings, "allow_scenario_commands", True, raising=False)

    async def fake(cmd, cwd, env=None, timeout=180):
        return 0, "22/tcp open ssh\n", ""

    monkeypatch.setattr(r, "_run_cmd_async", fake)
    h, uid = _login(client)

    # 1. Estado inicial: sin progreso
    dash = client.get(f"/api/students/{uid}/dashboard", headers=h).json()
    assert dash["general_percent"] == 0 and dash["completed_modules"] == 0
    assert dash["total_modules"] == 6 and len(dash["modules"]) == 6

    # 2. Abrir módulo: ningún checkpoint completado todavía
    mod = client.get(f"/api/modules/S01?user_id={uid}", headers=h).json()
    cps = [c["id"] for c in mod["checkpoints"]]
    assert cps and not any(c["completed"] for c in mod["checkpoints"])

    # 3. Escenario: iniciar, ejecutar comando, detener
    assert client.post("/api/scenarios/S01/start", json={}, headers=h).json()["status"] == "running"
    out = client.post("/api/scenarios/S01/command", json={"scenario_id": "S01", "command": "nmap -p 22 recon-lab"}, headers=h)
    assert out.json()["output"].startswith("22/tcp")

    # 4. Completar 2 checkpoints
    for cp in cps[:2]:
        body = {"student_id": uid, "module_id": "S01", "checkpoint_id": cp, "evidence": "evidencia", "status": "done"}
        assert client.post("/api/checkpoints/submit", json=body, headers=h).status_code == 200

    # 5. El progreso se refleja en el dashboard...
    dash = client.get(f"/api/students/{uid}/dashboard", headers=h).json()
    s01 = next(m for m in dash["modules"] if m["id"] == "S01")
    assert s01["progress"]["completed_checkpoints"] == 2
    assert s01["progress"]["total_checkpoints"] == len(cps)
    assert s01["progress"]["percent"] == round(2 / len(cps) * 100, 1)
    assert 0 < dash["general_percent"] < 100
    assert dash["points"] == 20

    # 6. ...y al volver a abrir el módulo, los checkpoints siguen marcados
    mod = client.get("/api/modules/S01", headers=h).json()
    assert [c["completed"] for c in mod["checkpoints"]][:2] == [True, True]

    # 7. Encuesta: exige consentimiento y luego se guarda
    survey = {"student_id": uid, "module_id": "S01", "responses": {"q1": 5}, "rating": 5, "comments": ""}
    assert client.post("/api/surveys/submit", json=survey, headers=h).status_code == 403
    assert client.post("/api/consent", json={"accepted": True}, headers=h).status_code == 200
    assert client.post("/api/surveys/submit", json=survey, headers=h).status_code == 200
    assert client.get("/api/modules/S01", headers=h).json()["survey_completed"] is True

    # 8. Completar todo el módulo suma una insignia
    for cp in cps[2:]:
        body = {"student_id": uid, "module_id": "S01", "checkpoint_id": cp, "evidence": "e", "status": "done"}
        client.post("/api/checkpoints/submit", json=body, headers=h)
    dash = client.get(f"/api/students/{uid}/dashboard", headers=h).json()
    assert dash["completed_modules"] == 1 and dash["badges"] == 1

    # 9. Reporte PDF
    pdf = client.get(f"/api/students/{uid}/report.pdf", headers=h)
    assert pdf.status_code == 200 and pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")

    # 10. El docente ve las métricas reales
    th, _ = _login(client, "teacher", "dev@uv.edu.co")
    metrics = client.get("/api/teacher/survey-metrics", headers=th).json()
    assert metrics["modules"][0] == {"module_id": "S01", "responses": 1, "avg_rating": 5.0}


def test_module_progress_uses_token_not_query_user(client):
    """Otro estudiante no puede ver el progreso ajeno cambiando ?user_id=."""
    h_a, uid_a = _login(client, email="a@uv.edu.co")
    h_b, _ = _login(client, email="b@uv.edu.co")
    cp = client.get("/api/modules/S01", headers=h_a).json()["checkpoints"][0]["id"]
    client.post("/api/checkpoints/submit", json={"student_id": uid_a, "module_id": "S01", "checkpoint_id": cp, "status": "done", "evidence": "x"}, headers=h_a)
    seen_by_b = client.get(f"/api/modules/S01?user_id={uid_a}", headers=h_b).json()
    assert not any(c["completed"] for c in seen_by_b["checkpoints"])


def _fields_read(filenames, pattern):
    found = set()
    for name in filenames:
        found |= set(re.findall(pattern, (PAGES / name).read_text(encoding="utf-8")))
    return found


def test_dashboard_fields_read_by_ui_exist_in_backend_schema():
    """Todo `data?.campo` de Dashboard/Resultados debe existir en StudentDashboard."""
    used = _fields_read(["Dashboard.jsx", "Results.jsx"], r"\bdata\??\.([a-z_]+)")
    assert used, "no se detectaron campos; revisa el patrón"
    missing = used - set(StudentDashboard.model_fields)
    assert not missing, f"La interfaz lee campos que el backend no devuelve: {sorted(missing)}"


def test_module_progress_fields_read_by_ui_exist_in_backend_schema():
    used = _fields_read(["Dashboard.jsx", "Results.jsx"], r"progress\??\.([a-z_]+)")
    assert used
    missing = used - set(ModuleProgressView.model_fields)
    assert not missing, f"La interfaz lee progress.* inexistentes: {sorted(missing)}"
    module_fields = _fields_read(["Dashboard.jsx"], r"\b(?:module|m)\??\.(id|title|titulo|description)\b")
    assert module_fields - {"titulo"} <= set(DashboardModule.model_fields)
