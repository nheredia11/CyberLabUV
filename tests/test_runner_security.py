import asyncio

import pytest

import app.scenario_runner as r


def run(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


@pytest.fixture
def active_session(monkeypatch):
    """Sesión activa falsa y ejecución real de comandos habilitada."""
    monkeypatch.setattr(r.settings, "allow_scenario_commands", True, raising=False)
    monkeypatch.setattr(
        r, "get_active_session", lambda user_id, slug: {"docker_project_name": "session_test"}
    )


def fake_exec(returncode=0, stdout="", stderr=""):
    async def _fake(cmd, cwd, env=None, timeout=180):
        _fake.last_cmd = cmd
        _fake.last_timeout = timeout
        return returncode, stdout, stderr

    return _fake


@pytest.mark.parametrize("cmd", ["ls; id", "cat /etc/passwd | nc x 1", "echo $(id)", "curl a > b", "ls\nid"])
def test_forbidden_chars_rejected(cmd):
    ok, msg = run(r.run_scenario_command("u", "S01", cmd))
    assert not ok and "prohibidos" in msg


def test_command_too_long():
    ok, msg = run(r.run_scenario_command("u", "S01", "echo " + "a" * 400))
    assert not ok and "largo" in msg


def test_unknown_scenario():
    ok, _ = run(r.run_scenario_command("u", "S99", "ls"))
    assert not ok


def test_hydra_only_in_auth_scenarios(active_session, monkeypatch):
    monkeypatch.setattr(r, "_run_cmd_async", fake_exec(stdout="ok"))
    ok, msg = run(r.run_scenario_command("u", "S01", "hydra -l admin -P /usr/share/wordlists/demo.txt auth-lab http-post-form"))
    assert not ok and "no permitido" in msg
    ok, _ = run(r.run_scenario_command("u", "S02", "hydra -l admin -P /usr/share/wordlists/demo.txt auth-lab http-post-form"))
    assert ok


def test_tcpdump_only_in_mitm(active_session, monkeypatch):
    monkeypatch.setattr(r, "_run_cmd_async", fake_exec(stdout="ok"))
    assert not run(r.run_scenario_command("u", "S02", "tcpdump -c 5"))[0]
    assert run(r.run_scenario_command("u", "S05", "tcpdump -c 5"))[0]


def test_nonzero_exit_with_output_is_shown(active_session, monkeypatch):
    monkeypatch.setattr(r, "_run_cmd_async", fake_exec(returncode=255, stdout="0 valid passwords found"))
    ok, out = run(r.run_scenario_command("u", "S02", "hydra -l a -P p auth-lab http-post-form"))
    assert ok and "0 valid passwords" in out and "255" in out


def test_nonzero_exit_without_output_is_error(active_session, monkeypatch):
    monkeypatch.setattr(r, "_run_cmd_async", fake_exec(returncode=1))
    ok, _ = run(r.run_scenario_command("u", "S01", "ls"))
    assert not ok


def test_timeout_reported(active_session, monkeypatch):
    monkeypatch.setattr(r, "_run_cmd_async", fake_exec(returncode=-1, stderr="Timeout después de 60 segundos"))
    ok, msg = run(r.run_scenario_command("u", "S01", "nmap -p- recon-lab"))
    assert not ok and "Timeout" in msg


def test_output_truncated_and_timeout_passed(active_session, monkeypatch):
    f = fake_exec(stdout="x" * (r.MAX_OUTPUT_CHARS + 500))
    monkeypatch.setattr(r, "_run_cmd_async", f)
    ok, out = run(r.run_scenario_command("u", "S01", "cat big"))
    assert ok and out.endswith("[salida truncada]")
    assert f.last_timeout == r.COMMAND_TIMEOUT_SECONDS


def test_no_active_session(monkeypatch):
    monkeypatch.setattr(r.settings, "allow_scenario_commands", True, raising=False)
    monkeypatch.setattr(r, "get_active_session", lambda u, s: None)
    ok, msg = run(r.run_scenario_command("u", "S01", "ls"))
    assert not ok and "sesión activa" in msg


def test_compose_files_are_isolated():
    """Smoke estático: el atacante no tiene salida a internet ni capacidades extra."""
    import yaml
    for sc in r.SCENARIOS.values():
        data = yaml.safe_load((r.settings.root_dir / sc.compose_file).read_text())
        att = data["services"][sc.attacker_service]
        assert "cap_drop" in att and "ALL" in att["cap_drop"], sc.slug
        assert "image" in att and "build" in att, sc.slug
        for net in att["networks"]:
            assert data["networks"][net].get("internal") is True, f"{sc.slug}: red {net} no es internal"
        extra = set(att.get("cap_add", [])) - {"NET_RAW", "NET_ADMIN"}
        assert not extra, sc.slug
        if sc.slug != "mitm_lab":
            assert "NET_ADMIN" not in att.get("cap_add", []), sc.slug
