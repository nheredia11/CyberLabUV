from __future__ import annotations
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    # Configurar entorno de pruebas limpio
    monkeypatch.setenv("ENABLE_DEV_LOGIN", "true")
    monkeypatch.setenv("TEACHER_EMAILS", "docente@uv.edu.co,dev@uv.edu.co")
    monkeypatch.setenv("ALLOW_SCENARIO_COMMANDS", "false")
    
    # Base de datos temporal para pruebas
    db_file = tmp_path / "test_cyberlab.db"
    import app.database as db_mod
    monkeypatch.setattr(db_mod, "DATABASE_PATH", str(db_file), raising=False)
    db_mod.init_db()

    # Limpiar caché de configuración si existe
    try:
        from app.config import get_settings
        get_settings.cache_clear()
    except AttributeError:
        pass

@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c