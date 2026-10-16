from __future__ import annotations
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def temp_db(monkeypatch, tmp_path):
    db_file = tmp_path / "test_cyberlab.db"
    import app.database as db_mod
    monkeypatch.setattr(db_mod, "DATABASE_PATH", str(db_file), raising=False)
    db_mod.init_db()

@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c