"""Proxy /labs/<sesión>/: acceso web a los laboratorios desde cualquier lugar.

Se levanta la app real del laboratorio en un hilo y el proxy se dirige a ella.
"""
import importlib.util
import os
import pathlib
import socket
import sys
import threading
import time
from urllib.parse import urlparse, parse_qs

import pytest
from werkzeug.serving import make_server

import app.scenario_runner as r
import app.routers.labs as labs_router
from app.auth import create_session
from app.lab_access import make_ticket, sign
from helpers import FakeDocker

LAB = pathlib.Path(__file__).resolve().parent.parent / "scenarios" / "common" / "edu_lab" / "app.py"


@pytest.fixture(scope="module")
def lab_server():
    os.environ["LAB_MODE"] = "auth_http"
    spec = importlib.util.spec_from_file_location("edu_lab_proxy", LAB)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # Flask ubica templates/ y static/ con el módulo
    spec.loader.exec_module(mod)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = make_server("127.0.0.1", port, mod.app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()


@pytest.fixture
def started(client, monkeypatch, lab_server):
    """Estudiante con S02 iniciado; el proxy apunta al laboratorio de prueba."""
    monkeypatch.setattr(r, "_run_cmd_async", FakeDocker())

    async def target(project, scenario):
        return lab_server

    monkeypatch.setattr(labs_router, "resolve_lab_target", target)
    h = {"Authorization": "Bearer " + create_session("est_lab", "student", "l@uv.edu.co")}
    start = client.post("/api/scenarios/S02/start", json={}, headers=h).json()
    assert start["status"] == "running" and start["lab_path"] == f"/labs/{start['session_id']}/"
    return h, start["session_id"]


def _open(client, h, scenario="S02"):
    link = client.post(f"/api/scenarios/{scenario}/lab-link", headers=h)
    assert link.status_code == 200, link.text
    res = client.get(link.json()["lab_url"], follow_redirects=False)
    assert res.status_code == 303
    return res


def test_ticket_sets_cookie_and_page_is_served_under_prefix(client, started):
    h, sid = started
    res = _open(client, h)
    assert res.headers["location"] == f"/labs/{sid}/"
    cookie = res.headers["set-cookie"]
    assert f"Path=/labs/{sid}/" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie

    page = client.get(f"/labs/{sid}/")
    assert page.status_code == 200
    # enlaces y formularios de la página llevan el prefijo del proxy
    assert f'action="/labs/{sid}/auth' in page.text
    assert f'href="/labs/{sid}/static/styles.css"' in page.text
    assert client.get(f"/labs/{sid}/static/styles.css").status_code == 200


def test_login_redirect_stays_inside_the_prefix(client, started):
    h, sid = started
    _open(client, h)
    res = client.post(f"/labs/{sid}/auth-http/login", data={"username": "estudiante", "password": "x"}, follow_redirects=False)
    assert res.status_code == 302
    loc = urlparse(res.headers["location"])
    assert loc.path == f"/labs/{sid}/" and parse_qs(loc.query) == {"auth": ["fail"]}


def test_without_cookie_or_with_bad_ticket_is_rejected(client, started):
    h, sid = started
    assert client.get(f"/labs/{sid}/").status_code == 401
    assert client.get(f"/labs/{sid}/?ticket=basura").status_code == 403


def test_another_student_cannot_use_or_forge_access(client, started):
    h, sid = started
    other = {"Authorization": "Bearer " + create_session("otro_lab", "student", "o@uv.edu.co")}
    # no tiene sesión de S02 propia
    assert client.post("/api/scenarios/S02/lab-link", headers=other).status_code == 409
    # un ticket firmado para OTRO usuario no abre la sesión ajena
    forged = make_ticket("otro_lab", sid)
    assert client.get(f"/labs/{sid}/?ticket={forged}", follow_redirects=False).status_code == 403
    # una cookie de otro usuario tampoco
    client.cookies.set(f"cyberlab_lab_{sid}", sign({"k": "cookie", "uid": "otro_lab", "sid": sid, "exp": time.time() + 600}))
    assert client.get(f"/labs/{sid}/").status_code == 401


def test_ticket_for_one_session_does_not_open_another(client, started):
    h, sid = started
    ticket = make_ticket("est_lab", "otra-sesion")
    assert client.get(f"/labs/{sid}/?ticket={ticket}", follow_redirects=False).status_code == 403


def test_expired_ticket_is_rejected(client, started):
    h, sid = started
    old = sign({"k": "ticket", "uid": "est_lab", "sid": sid, "exp": time.time() - 1})
    assert client.get(f"/labs/{sid}/?ticket={old}", follow_redirects=False).status_code == 403


def test_stopped_session_is_no_longer_reachable(client, started):
    h, sid = started
    _open(client, h)
    assert client.post("/api/scenarios/S02/stop", json={}, headers=h).status_code == 200
    assert client.get(f"/labs/{sid}/").status_code == 404


def test_lab_link_requires_a_running_scenario(client):
    h = {"Authorization": "Bearer " + create_session("sin_lab", "student", "s@uv.edu.co")}
    assert client.post("/api/scenarios/S01/lab-link", headers=h).status_code == 409
    assert client.post("/api/scenarios/S99/lab-link", headers=h).status_code == 404


def test_student_credentials_are_not_forwarded_to_the_lab(client, started, monkeypatch):
    """El laboratorio es vulnerable a propósito: nunca debe recibir el token ni las cookies de la plataforma."""
    h, sid = started
    _open(client, h)
    seen = {}

    class Spy:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False
        async def request(self, method, url, params=None, content=None, headers=None):
            seen.update(headers)
            import httpx
            return httpx.Response(200, content=b"ok")

    monkeypatch.setattr(labs_router.httpx, "AsyncClient", Spy)
    client.get(f"/labs/{sid}/", headers={"Authorization": h["Authorization"]})
    lowered = {k.lower() for k in seen}
    assert "authorization" not in lowered and "cookie" not in lowered
    assert seen["X-Forwarded-Prefix"] == f"/labs/{sid}"


def test_lab_page_csp_allows_its_styles_but_not_inline_scripts(client, started):
    """Regresión: la CSP global (default-src 'none') bloqueaba el CSS y el JS del laboratorio."""
    h, sid = started
    _open(client, h)
    page = client.get(f"/labs/{sid}/")
    csp = page.headers["content-security-policy"]
    assert "style-src 'self'" in csp and "script-src 'self'" in csp
    assert "unsafe-inline" not in csp and "frame-ancestors 'none'" in csp
    # la API conserva la política estricta
    assert client.get("/health").headers["content-security-policy"].startswith("default-src 'none'")


def test_lab_page_loads_its_script_and_hides_internal_details(client, started):
    h, sid = started
    _open(client, h)
    page = client.get(f"/labs/{sid}/").text
    assert f'src="/labs/{sid}/static/lab.js"' in page
    assert client.get(f"/labs/{sid}/static/lab.js").status_code == 200
    assert "192.168." not in page and "docker compose" not in page
