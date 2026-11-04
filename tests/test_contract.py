"""Contrato backend <-> frontend.

1. El esquema OpenAPI no cambia sin que alguien lo decida (snapshot versionado).
2. Toda ruta que el frontend usa en lib/api.js existe en el backend con ese método.
3. Los endpoints de escenarios devuelven exactamente los campos que el frontend lee.
"""
import json
import pathlib
import re

from app.auth import create_session
from app.main import app

ROOT = pathlib.Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "backend" / "openapi.snapshot.json"
API_JS = ROOT / "frontend" / "src" / "lib" / "api.js"


def test_openapi_matches_snapshot():
    current = json.loads(json.dumps(app.openapi(), sort_keys=True))
    expected = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    assert current == expected, (
        "El contrato de la API cambió. Si es intencional ejecuta: "
        "PYTHONPATH=backend python scripts/export_openapi.py y revisa el diff junto con el frontend."
    )


def _frontend_calls():
    """Extrae (método, ruta) de las llamadas request(`/api/...`) de lib/api.js."""
    text = API_JS.read_text(encoding="utf-8")
    calls = []
    for m in re.finditer(r"request\(\s*[`'\"](/api/[^`'\"]*)", text):
        raw = re.sub(r"\$\{buildQuery\(.*?\)\}", "", m.group(1))  # ?query no es parte de la ruta
        path = re.sub(r"\$\{[^}]*\}", "{x}", raw)
        window = text[m.end(): m.end() + 200]
        method = re.search(r"method:\s*['\"](\w+)['\"]", window)
        calls.append(((method.group(1) if method else "GET").upper(), path))
    return calls


def _path_regex(openapi_path: str):
    return re.compile("^" + re.sub(r"\{[^}]+\}", r"[^/]+", openapi_path) + "$")


def test_frontend_routes_exist_in_backend():
    paths = json.loads(SNAPSHOT.read_text(encoding="utf-8"))["paths"]
    calls = _frontend_calls()
    assert len(calls) >= 10, "No se detectaron llamadas del frontend; revisa el parser."
    missing = []
    for method, fpath in calls:
        concrete = fpath.replace("{x}", "x")
        ok = any(
            _path_regex(p).match(concrete) and method.lower() in ops
            for p, ops in paths.items()
        )
        if not ok:
            missing.append(f"{method} {fpath}")
    assert not missing, f"El frontend llama rutas inexistentes en el backend: {missing}"


def test_scenario_responses_have_declared_fields(client, monkeypatch):
    import app.scenario_runner as r

    monkeypatch.setattr(r.settings, "allow_scenario_commands", True, raising=False)

    async def fake(cmd, cwd, env=None, timeout=180):
        return 0, "salida\n", ""

    monkeypatch.setattr(r, "_run_cmd_async", fake)
    h = {"Authorization": "Bearer " + create_session("contract_user", "student", "c@uv.edu.co")}

    start = client.post("/api/scenarios/S01/start", json={}, headers=h).json()
    assert {"scenario_id", "action", "status", "message", "local_url", "session_id"} <= set(start)

    cmd = client.post("/api/scenarios/S01/command", json={"scenario_id": "S01", "command": "ls"}, headers=h).json()
    assert set(cmd) == {"status", "output"}

    status = client.post("/api/scenarios/S01/status", json={}, headers=h).json()
    assert status["status"] == "running" and status["local_url"].startswith("http://127.0.0.1:")
