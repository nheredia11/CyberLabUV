"""Control de acceso (OWASP ASVS V4): cada ruta de la API tiene una política explícita.

Si agregas una ruta nueva, esta prueba falla hasta que la clasifiques aquí.
"""
import re
from datetime import datetime, timedelta, timezone

import pytest

from app.auth import create_session
from app.database import get_db_connection

PUBLIC = {
    "/health",
    "/api/auth/login", "/api/auth/google", "/api/auth/dev-login", "/api/auth/logout",
    "/api/catalog", "/api/catalog/{module_id}", "/api/modules", "/api/modules/{module_id}",
}
TEACHER_ONLY = {
    "/api/teacher/analytics", "/api/teacher/export.csv",
    "/api/teacher/notes", "/api/teacher/survey-metrics",
}
# Rutas con dueño: el estudiante solo accede a lo suyo; el docente a todo.
OWNED = [
    "/api/students/{other}/dashboard",
    "/api/students/{other}/report",
    "/api/students/{other}/report.pdf",
    "/api/modules/S01/feedback?user_id={other}",
]


def _routes(app):
    for path, ops in app.openapi()["paths"].items():
        for method in ops:
            if method in ("get", "post"):
                yield method, path


def _concrete(path):
    return re.sub(r"\{[^}]+\}", "S01", path)


@pytest.fixture
def tokens():
    return {
        "student": {"Authorization": "Bearer " + create_session("est_a", "student", "a@uv.edu.co")},
        "teacher": {"Authorization": "Bearer " + create_session("doc_a", "teacher", "dev@uv.edu.co")},
    }


def test_every_route_has_an_explicit_policy(client):
    from app.main import app
    known = PUBLIC | TEACHER_ONLY
    protected = {p for _, p in _routes(app)} - known
    # Lo no clasificado como público/docente exige sesión: se lista para que sea una decisión consciente.
    assert protected == {
        "/api/checkpoints/submit", "/api/consent", "/api/modules/{module_id}/feedback",
        "/api/modules/{module_id}/surveys", "/api/scenarios/{scenario_id}/command",
        "/api/scenarios/{scenario_id}/{action}", "/api/students/{student_id}/dashboard",
        "/api/students/{student_id}/report", "/api/students/{student_id}/report.pdf",
        "/api/surveys/responses", "/api/surveys/submit",
    }, "Hay rutas nuevas: clasifícalas en PUBLIC / TEACHER_ONLY / lista de protegidas."


def test_anonymous_cannot_reach_protected_routes(client):
    from app.main import app
    for method, path in _routes(app):
        if path in PUBLIC:
            continue
        res = getattr(client, method)(_concrete(path), **({"json": {}} if method == "post" else {}))
        assert res.status_code == 401, f"{method.upper()} {path} respondió {res.status_code} sin sesión"


def test_students_cannot_reach_teacher_routes(client, tokens):
    for path in TEACHER_ONLY:
        for method in ("get", "post"):
            res = getattr(client, method)(_concrete(path), headers=tokens["student"], **({"json": {}} if method == "post" else {}))
            if res.status_code == 405:
                continue
            assert res.status_code == 403, f"{method.upper()} {path} respondió {res.status_code} a un estudiante"


@pytest.mark.parametrize("template", OWNED)
def test_students_cannot_read_other_students_data(client, tokens, template):
    url = template.format(other="otro_alumno")
    assert client.get(url, headers=tokens["student"]).status_code == 403
    assert client.get(url, headers=tokens["teacher"]).status_code == 200


def test_dev_login_is_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv("ENABLE_DEV_LOGIN", raising=False)
    assert client.post("/api/auth/dev-login").status_code == 403
    assert client.post("/api/auth/login", json={"email": "dev@uv.edu.co"}).status_code == 403


def test_logout_revokes_the_token(client, tokens):
    h = tokens["student"]
    assert client.get("/api/consent", headers=h).status_code == 200
    assert client.post("/api/auth/logout", headers=h).status_code == 200
    assert client.get("/api/consent", headers=h).status_code == 401


def test_expired_session_is_rejected(client, tokens):
    h = tokens["student"]
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    with get_db_connection() as conn:
        conn.execute("UPDATE sessions SET expires_at = ?", (past,))
        conn.commit()
    assert client.get("/api/consent", headers=h).status_code == 401


def test_tampered_token_is_rejected(client):
    assert client.get("/api/consent", headers={"Authorization": "Bearer " + "a" * 43}).status_code == 401
    assert client.get("/api/consent", headers={"Authorization": "Bearer dev-teacher-token"}).status_code == 401


def test_security_headers_present(client):
    h = client.get("/health").headers
    assert h.get("x-content-type-options") == "nosniff"
    assert "x-frame-options" in h


def test_legacy_users_endpoint_is_gone(client, tokens):
    """Stub eliminado: devolvía usuarios inventados a cualquier sesión."""
    assert client.get("/api/users", headers=tokens["teacher"]).status_code == 404
