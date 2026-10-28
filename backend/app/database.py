from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional, Dict

from .config import get_settings

# Aseguramos que sea un objeto Path explícito
DATABASE_PATH = Path(get_settings().absolute_database_path if hasattr(get_settings(), 'absolute_database_path') else get_settings().database_path)

SCHEMA = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student','teacher')),
    avatar TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS consents (
    user_id TEXT PRIMARY KEY,
    accepted_at TEXT NOT NULL,
    version TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    email TEXT NOT NULL,
    expires_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkpoint_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    checkpoint_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending','done','review')),
    evidence TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, module_id, checkpoint_id)
);

CREATE TABLE IF NOT EXISTS surveys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    answers_json TEXT NOT NULL,
    rating INTEGER,
    comments TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenario_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_id TEXT NOT NULL,
    student_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS terminal_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL,
    command TEXT NOT NULL,
    status TEXT NOT NULL,
    output TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS practice_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    scenario_slug TEXT NOT NULL,
    docker_project_name TEXT NOT NULL,
    assigned_ports TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'starting',
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    ended_at TEXT NULL
);
"""

DEFAULT_USERS = [
    {"id": "ana", "name": "Ana Rodríguez", "email": "ana.rodriguez@uv.edu.co", "role": "student", "avatar": "AR"},
    {"id": "carlos", "name": "Prof. Carlos M.", "email": "carlos.m@uv.edu.co", "role": "teacher", "avatar": "CM"},
]

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# Alias de compatibilidad requerido por storage.py y otros módulos
get_db_connection = connect

def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        # Migración defensiva: asegurar la columna expires_at en tablas existentes
        try:
            conn.execute("ALTER TABLE sessions ADD COLUMN expires_at TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # La columna ya existe, se ignora de forma segura

        for user in DEFAULT_USERS:
            conn.execute(
                """INSERT OR IGNORE INTO users(id, name, email, role, avatar, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (user["id"], user["name"], user["email"], user["role"], user["avatar"], utcnow()),
            )

def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None

def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]

def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)

def loads(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    return json.loads(value)

def create_practice_session(
    session_id: str,
    user_id: str,
    scenario_slug: str,
    docker_project_name: str,
    assigned_ports: Any,
    expires_at: str,
) -> dict[str, Any]:
    ports_str = json.dumps(assigned_ports) if isinstance(assigned_ports, (dict, list)) else str(assigned_ports)
    now = utcnow()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO practice_sessions 
            (id, user_id, scenario_slug, docker_project_name, assigned_ports, status, started_at, expires_at)
            VALUES (?, ?, ?, ?, ?, 'running', ?, ?)
            """,
            (session_id, user_id, scenario_slug, docker_project_name, ports_str, now, expires_at)
        )
    return get_session_by_id(session_id) or {}

def get_active_session(user_id: str, scenario_slug: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, scenario_slug, docker_project_name, assigned_ports,
                   status, started_at, expires_at, ended_at
            FROM practice_sessions
            WHERE user_id = ? AND scenario_slug = ? AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
            """,
            (user_id, scenario_slug),
        )
        row = cursor.fetchone()
        if not row:
            return None
        session_dict = dict(row)
        session_dict["assigned_ports"] = json.loads(session_dict["assigned_ports"])
        return session_dict

def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, scenario_slug, docker_project_name, assigned_ports,
                   status, started_at, expires_at, ended_at
            FROM practice_sessions
            WHERE id = ?
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        session_dict = dict(row)
        session_dict["assigned_ports"] = json.loads(session_dict["assigned_ports"])
        return session_dict

def update_session_status(session_id: str, status: str) -> Optional[Dict[str, Any]]:
    terminal_statuses = {"completed", "stopped", "expired", "error"}
    ended_at = utcnow() if status in terminal_statuses else None

    with connect() as conn:
        conn.execute(
            """
            UPDATE practice_sessions
            SET status = ?, ended_at = COALESCE(?, ended_at)
            WHERE id = ?
            """,
            (status, ended_at, session_id),
        )
    return get_session_by_id(session_id)

def get_expired_running_sessions() -> list[Dict[str, Any]]:
    now_iso = utcnow()
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, scenario_slug, docker_project_name, assigned_ports,
                   status, started_at, expires_at
            FROM practice_sessions
            WHERE status = 'running' AND expires_at <= ?
            """,
            (now_iso,),
        )
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            session_dict = dict(row)
            session_dict["assigned_ports"] = json.loads(session_dict["assigned_ports"])
            sessions.append(session_dict)
        return sessions
    
def create_practice_session(
    session_id: str,
    user_id: str,
    scenario_slug: str,
    docker_project_name: str,
    assigned_ports: Any,
    expires_at: str,
) -> dict[str, Any]:
    """Crea o reemplaza una sesión de práctica persistente con UUID completo."""
    ports_str = json.dumps(assigned_ports) if isinstance(assigned_ports, (dict, list)) else str(assigned_ports)
    now = utcnow()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO practice_sessions 
            (id, user_id, scenario_slug, docker_project_name, assigned_ports, status, started_at, expires_at)
            VALUES (?, ?, ?, ?, ?, 'running', ?, ?)
            """,
            (session_id, user_id, scenario_slug, docker_project_name, ports_str, now, expires_at)
        )
    return get_session_by_id(session_id) or {}

def get_active_session(user_id: str, scenario_slug: str) -> Optional[Dict[str, Any]]:
    """Obtiene la sesión activa ('running') más reciente de un estudiante para un escenario."""
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, scenario_slug, docker_project_name, assigned_ports,
                   status, started_at, expires_at, ended_at
            FROM practice_sessions
            WHERE user_id = ? AND scenario_slug = ? AND status = 'running'
            ORDER BY started_at DESC LIMIT 1
            """,
            (user_id, scenario_slug),
        )
        row = cursor.fetchone()
        if not row:
            return None
        session_dict = dict(row)
        session_dict["assigned_ports"] = json.loads(session_dict["assigned_ports"])
        return session_dict

def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Busca una sesión por su UUID completo."""
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, scenario_slug, docker_project_name, assigned_ports,
                   status, started_at, expires_at, ended_at
            FROM practice_sessions
            WHERE id = ?
            """,
            (session_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        session_dict = dict(row)
        session_dict["assigned_ports"] = json.loads(session_dict["assigned_ports"])
        return session_dict

def update_session_status(session_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Actualiza el estado de una sesión de práctica e inserta ended_at si es terminal."""
    terminal_statuses = {"completed", "stopped", "expired", "error"}
    ended_at = utcnow() if status in terminal_statuses else None

    with connect() as conn:
        conn.execute(
            """
            UPDATE practice_sessions
            SET status = ?, ended_at = COALESCE(?, ended_at)
            WHERE id = ?
            """,
            (status, ended_at, session_id),
        )
    return get_session_by_id(session_id)

def get_expired_running_sessions() -> list[Dict[str, Any]]:
    """Obtiene todas las sesiones 'running' cuyo tiempo asignado ya expiró."""
    now_iso = utcnow()
    with connect() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, scenario_slug, docker_project_name, assigned_ports,
                   status, started_at, expires_at
            FROM practice_sessions
            WHERE status = 'running' AND expires_at <= ?
            """,
            (now_iso,),
        )
        rows = cursor.fetchall()
        sessions = []
        for row in rows:
            session_dict = dict(row)
            session_dict["assigned_ports"] = json.loads(session_dict["assigned_ports"])
            sessions.append(session_dict)
        return sessions