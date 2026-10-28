from app.auth import create_session

def test_scenario_start_stop_flow(client, monkeypatch):
    import app.scenario_runner as r
    monkeypatch.setenv("ALLOW_SCENARIO_COMMANDS", "true")
    from app.config import get_settings; get_settings.cache_clear()
    
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
    
    # 3. Stop
    res = client.post("/api/scenarios/S01/stop", json={}, headers=h)
    assert res.status_code == 200, res.text