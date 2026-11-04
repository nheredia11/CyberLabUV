"""Los payloads de estas pruebas se construyen con las MISMAS claves que genera lib/api.js.

Regresión: las encuestas de la interfaz devolvían 422 siempre porque las pruebas usaban otra ruta y
otro formato que los que realmente envía el frontend.
"""
import pathlib
import re

import pytest

import app.scenario_runner as r
from app.auth import create_session

API_JS = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "src" / "lib" / "api.js"


def _keys_built_by(function_name: str) -> set[str]:
    text = API_JS.read_text(encoding="utf-8")
    start = text.index(f"function {function_name}(")
    body = text[start: text.index("\n}\n", start)]
    return set(re.findall(r"^ {4}(\w+):", body, re.M))


def survey_payload(user_id, module_id="S01", rating=4.33):
    """Misma forma que normalizeSurveyPayload() de lib/api.js."""
    payload = {
        "user_id": user_id, "student_id": user_id, "module_id": module_id,
        "answers": {"q1": 4, "q2": 5, "q3": 4}, "answers_json": {"q1": 4, "q2": 5, "q3": 4},
        "rating": rating, "comments": "",
    }
    assert set(payload) == _keys_built_by("normalizeSurveyPayload"), "api.js cambió: actualiza este payload"
    return payload


def checkpoint_payload(user_id, module_id, checkpoint_id):
    """Misma forma que normalizeCheckpointPayload() de lib/api.js."""
    payload = {
        "user_id": user_id, "student_id": user_id, "module_id": module_id,
        "checkpoint_id": checkpoint_id, "evidence": "mi evidencia", "status": "done", "completed": True,
    }
    assert set(payload) == _keys_built_by("normalizeCheckpointPayload"), "api.js cambió: actualiza este payload"
    return payload


@pytest.fixture
def student(client):
    h = {"Authorization": "Bearer " + create_session("est_p", "student", "p@uv.edu.co")}
    assert client.post("/api/consent", json={"accepted": True}, headers=h).status_code == 200
    return h


@pytest.mark.parametrize("path", ["/api/modules/S01/surveys", "/api/surveys/responses", "/api/surveys/submit"])
def test_survey_from_the_ui_is_saved_on_every_route(client, student, path):
    res = client.post(path, json=survey_payload("est_p"), headers=student)
    assert res.status_code == 200, res.text


def test_decimal_likert_average_is_stored_and_reported(client, student):
    assert client.post("/api/modules/S01/surveys", json=survey_payload("est_p", rating=4.33), headers=student).status_code == 200
    teacher = {"Authorization": "Bearer " + create_session("doc_p", "teacher", "dev@uv.edu.co")}
    m = client.get("/api/teacher/survey-metrics", headers=teacher).json()
    assert m["modules"][0]["avg_rating"] == 4.33


def test_path_module_wins_and_identity_comes_from_token(client, student):
    body = survey_payload("otro_usuario", module_id="S99")
    assert client.post("/api/modules/S02/surveys", json=body, headers=student).status_code == 200
    teacher = {"Authorization": "Bearer " + create_session("doc_p", "teacher", "dev@uv.edu.co")}
    modules = client.get("/api/teacher/survey-metrics", headers=teacher).json()["modules"]
    assert [m["module_id"] for m in modules] == ["S02"]
    assert client.get("/api/students/otro_usuario/dashboard", headers=teacher).json()["modules"][1]["progress"]["survey_completed"] is False


@pytest.mark.parametrize("bad", [{"rating": 0}, {"rating": 6}, {"comments": "x" * 2001}, {"module_id": "NO_EXISTE"}])
def test_invalid_surveys_are_rejected(client, student, bad):
    body = {**survey_payload("est_p"), **bad}
    assert client.post("/api/surveys/submit", json=body, headers=student).status_code == 422


def test_survey_requires_consent(client):
    h = {"Authorization": "Bearer " + create_session("sin_consent", "student", "s@uv.edu.co")}
    assert client.post("/api/modules/S01/surveys", json=survey_payload("sin_consent"), headers=h).status_code == 403


def test_checkpoint_from_the_ui_and_validation(client, student):
    cp = client.get("/api/modules/S01").json()["checkpoints"][0]["id"]
    assert client.post("/api/checkpoints/submit", json=checkpoint_payload("est_p", "S01", cp), headers=student).status_code == 200
    assert client.post("/api/checkpoints/submit", json=checkpoint_payload("est_p", "S01", "no-existe"), headers=student).status_code == 422
    assert client.post("/api/checkpoints/submit", json=checkpoint_payload("est_p", "NOPE", cp), headers=student).status_code == 422
    big = {**checkpoint_payload("est_p", "S01", cp), "evidence": "x" * 5001}
    assert client.post("/api/checkpoints/submit", json=big, headers=student).status_code == 422


def test_teacher_note_validation(client):
    teacher = {"Authorization": "Bearer " + create_session("doc_n", "teacher", "dev@uv.edu.co")}
    ok = {"student_id": "est_p", "module_id": "S01", "body": "Buen trabajo"}
    assert client.post("/api/teacher/notes", json=ok, headers=teacher).status_code == 200
    for bad in ({**ok, "body": ""}, {**ok, "body": "x" * 5001}, {"module_id": "S01", "body": "sin estudiante"}):
        assert client.post("/api/teacher/notes", json=bad, headers=teacher).status_code == 422


def test_session_limits_per_user_and_total(client, monkeypatch):
    async def fake(cmd, cwd, env=None, timeout=180):
        return 0, "ok", ""

    monkeypatch.setattr(r, "_run_cmd_async", fake)
    monkeypatch.setattr(r.settings, "max_sessions_per_user", 2, raising=False)
    monkeypatch.setattr(r.settings, "max_sessions_total", 3, raising=False)
    a = {"Authorization": "Bearer " + create_session("ua", "student", "ua@uv.edu.co")}
    b = {"Authorization": "Bearer " + create_session("ub", "student", "ub@uv.edu.co")}

    ok = lambda sid, h: client.post(f"/api/scenarios/{sid}/start", json={}, headers=h).json()  # noqa: E731
    assert ok("S01", a)["status"] == "running"
    assert ok("S02", a)["status"] == "running"
    third = ok("S03", a)
    assert third["status"] == "error" and "2 escenarios activos" in third["message"]
    assert ok("S01", a)["status"] == "running"          # recuperar una activa no cuenta como nueva
    assert ok("S01", b)["status"] == "running"          # total = 3
    full = ok("S02", b)
    assert full["status"] == "error" and "límite de capacidad" in full["message"]
