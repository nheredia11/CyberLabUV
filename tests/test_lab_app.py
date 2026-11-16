"""Pruebas de la aplicación de los laboratorios (scenarios/common/edu_lab/app.py)."""
import importlib.util
import pathlib
import socket
import sys
import struct
import threading
import time

import pytest

LAB = pathlib.Path(__file__).resolve().parent.parent / "scenarios" / "common" / "edu_lab" / "app.py"


@pytest.fixture(scope="module")
def lab():
    spec = importlib.util.spec_from_file_location("edu_lab_app", LAB)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # Flask ubica templates/ y static/ con el módulo
    spec.loader.exec_module(module)
    return module


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _read_banner(port):
    with socket.create_connection(("127.0.0.1", port), timeout=3) as c:
        return c.recv(100).decode().strip()


def test_banner_survives_aborted_connections(lab):
    """Regresión: un escaneo de nmap (conexiones cortadas con RST) mataba el servicio para todos."""
    port = _free_port()
    threading.Thread(target=lab.banner_server, args=(port, "SSH-2.0-Test"), daemon=True).start()
    for _ in range(50):
        try:
            assert _read_banner(port) == "SSH-2.0-Test"
            break
        except OSError:
            time.sleep(0.05)

    for _ in range(30):  # cortar abruptamente, como hace un escaneo
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack("ii", 1, 0))
        s.connect(("127.0.0.1", port))
        s.close()

    assert _read_banner(port) == "SSH-2.0-Test"


def test_login_redirect_signals_result(lab):
    """hydra distingue éxito/fallo por la redirección (?auth=ok / ?auth=fail)."""
    client = lab.app.test_client()
    bad = client.post("/auth-http/login", data={"username": "estudiante", "password": "x"})
    good = client.post("/auth-http/login", data={"username": lab.DEMO_USER, "password": lab.DEMO_PASSWORD})
    assert bad.status_code == 302 and "auth=fail" in bad.headers["Location"]
    assert good.status_code == 302 and "auth=ok" in good.headers["Location"]


def test_auth_http_page_shows_its_login_form(lab, monkeypatch):
    """Regresión: la página de S02 no tenía formulario (solo S04 lo mostraba)."""
    monkeypatch.setattr(lab, "LAB_MODE", "auth_http")
    page = lab.app.test_client().get("/").get_data(as_text=True)
    assert 'action="/auth-http/login"' in page
    ok = lab.app.test_client().get("/?auth=ok").get_data(as_text=True)
    assert "Acceso concedido" in ok
