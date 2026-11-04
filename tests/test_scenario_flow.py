from app.auth import create_session

def test_scenario_start_stop_flow(client, monkeypatch):
    import app.scenario_runner as r
    # r.settings se fija al importar el módulo; se fuerza la ejecución real (con Docker simulado).
    monkeypatch.setattr(r.settings, "allow_scenario_commands", True, raising=False)
    
    async def fake(cmd, cwd, env=None, timeout=180):
        return 0, "ok\n", ""
    monkeypatch.setattr(r, "_run_cmd_async", fake)
    
    h = {"Authorization": "Bearer " + create_session("student_a", "student", "a@uv.edu.co")}
    
    # 1. Start
    res = client.post("/api/scenarios/S01/start", json={}, headers=h)
    assert res.status_code == 200, res.text
    assert res.json()["local_url"].startswith("http://127.0.0.1:")
    
    # 2. Command
    res = client.post("/api/scenarios/S01/command", json={"scenario_id": "S01", "command": "nmap -p 80 recon-lab"}, headers=h)
    assert res.status_code == 200, res.text
    # Contrato con el frontend: la salida viaja en la clave "output".
    assert res.json()["output"] == "ok"

    # Sin sesión activa el backend responde 400 con un mensaje claro.
    h2 = {"Authorization": "Bearer " + create_session("student_b", "student", "b@uv.edu.co")}
    res = client.post("/api/scenarios/S02/command", json={"scenario_id": "S02", "command": "ls"}, headers=h2)
    assert res.status_code == 400 and "sesión activa" in res.json()["detail"]
    
    # 3. Stop
    res = client.post("/api/scenarios/S01/stop", json={}, headers=h)
    assert res.status_code == 200, res.text