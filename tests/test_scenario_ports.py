"""Puertos y limpieza de sesiones.

Regresión: el backend corre dentro de un contenedor y elegía puertos probando su propio 127.0.0.1,
así que dos escenarios podían recibir el mismo puerto del host ("port is already allocated").
"""
import re

import pytest
import yaml

import app.scenario_runner as r
from app.auth import create_session
from helpers import FakeDocker


@pytest.fixture
def student():
    return {"Authorization": "Bearer " + create_session("est_ports", "student", "p@uv.edu.co")}


def test_port_is_the_one_docker_published(client, student, monkeypatch):
    monkeypatch.setattr(r, "_run_cmd_async", FakeDocker(port="0.0.0.0:51234\n"))
    res = client.post("/api/scenarios/S01/start", json={}, headers=student).json()
    assert res["local_url"] == "http://127.0.0.1:51234"
    status = client.post("/api/scenarios/S01/status", json={}, headers=student).json()
    assert status["local_url"] == "http://127.0.0.1:51234"


def test_start_asks_docker_for_the_port_of_the_lab_service(client, student, monkeypatch):
    docker = FakeDocker()
    monkeypatch.setattr(r, "_run_cmd_async", docker)
    client.post("/api/scenarios/S03/start", json={}, headers=student)
    port_call = next(c for c in docker.calls if "port" in c)
    assert port_call[-2:] == ["web_owasp-lab", "5000"]
    assert docker.verbs() == ["up", "port"]


def test_failed_up_rolls_back_and_reports_error(client, student, monkeypatch):
    docker = FakeDocker(fail_up=True)
    monkeypatch.setattr(r, "_run_cmd_async", docker)
    res = client.post("/api/scenarios/S02/start", json={}, headers=student).json()
    assert res["status"] == "error" and "port is already allocated" in res["message"]
    assert docker.verbs() == ["up", "down"]          # no deja contenedores ni redes a medias
    assert client.post("/api/scenarios/S02/status", json={}, headers=student).json()["status"] == "stopped"


def test_unreadable_port_rolls_back(client, student, monkeypatch):
    docker = FakeDocker(fail_port=True)
    monkeypatch.setattr(r, "_run_cmd_async", docker)
    res = client.post("/api/scenarios/S01/start", json={}, headers=student).json()
    assert res["status"] == "error" and "puerto" in res["message"]
    assert docker.verbs() == ["up", "port", "down"]


@pytest.mark.parametrize("text,expected", [
    ("127.0.0.1:49153\n", 49153), ("0.0.0.0:8100", 8100), ("[::]:32768\n", 32768), ("", None), ("basura", None),
])
def test_parse_published_port(text, expected):
    assert r.parse_published_port(text) == expected


def test_restarting_attacker_gives_a_clear_message(monkeypatch):
    import asyncio
    monkeypatch.setattr(r.settings, "allow_scenario_commands", True, raising=False)
    monkeypatch.setattr(r, "get_active_session", lambda u, s: {"docker_project_name": "session_x"})

    async def fake(cmd, cwd, env=None, timeout=180):
        return 1, "", 'service "recon-attacker" is not running'

    monkeypatch.setattr(r, "_run_cmd_async", fake)
    ok, msg = asyncio.new_event_loop().run_until_complete(r.run_scenario_command("u", "S01", "ls"))
    assert not ok and "iniciando o reiniciando" in msg


def test_compose_ports_are_chosen_by_docker():
    """`127.0.0.1:${VAR:-}:5000` => con la variable vacía Docker asigna un puerto libre del host."""
    for sc in r.SCENARIOS.values():
        data = yaml.safe_load((r.settings.root_dir / sc.compose_file).read_text())
        mapping = data["services"][sc.lab_service]["ports"][0]
        assert re.fullmatch(r"127\.0\.0\.1:\$\{[A-Z_]+:-\}:5000", mapping), f"{sc.slug}: {mapping}"
