from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .config import get_settings

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
"""

DEFAULT_USERS = [
    {"id": "ana", "name": "Ana Rodríguez", "email": "ana.rodriguez@uv.edu.co", "role": "student", "avatar": "AR"},
    {"id": "carlos", "name": "Prof. Carlos M.", "email": "carlos.m@uv.edu.co", "role": "teacher", "avatar": "CM"},
]

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    db_path: Path = get_settings().database_path
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        for user in DEFAULT_USERS:
            conn.execute(
                """INSERT OR IGNORE INTO users(id, name, email, role, avatar, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user["id"], user["name"], user["email"], user["role"], user["avatar"], utcnow()),
            )
    init_practice_sessions_table()

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


# ============================================================
# PRACTICE SESSIONS - Aislamiento de escenarios Docker
# ============================================================

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from pathlib import Path

from .config import get_settings


def _get_practice_db_connection():
    """Conexión a SQLite usando la configuración central del proyecto."""
    db_path = get_settings().absolute_database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=15.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_practice_sessions_table() -> None:
    """Crea la tabla practice_sessions e índices si no existen."""
    with _get_practice_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS practice_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                scenario_slug TEXT NOT NULL,
                docker_project_name TEXT UNIQUE NOT NULL,
                assigned_ports TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'starting',
                started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                ended_at DATETIME NULL
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_scenario 
            ON practice_sessions(user_id, scenario_slug);
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_status_expires 
            ON practice_sessions(status, expires_at);
        """)
        conn.commit()


def create_practice_session(
    user_id: str,
    scenario_slug: str,
    docker_project_name: str,
    assigned_ports: Dict[str, int],
    duration_minutes: int = 60,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Crea una nueva sesión de práctica con UUID completo."""
    full_session_id = session_id if (session_id and len(session_id) == 36) else str(uuid.uuid4())
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=duration_minutes)
    ports_json = json.dumps(assigned_ports)

    with _get_practice_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO practice_sessions 
            (id, user_id, scenario_slug, docker_project_name, assigned_ports, status, started_at, expires_at)
            VALUES (?, ?, ?, ?, ?, 'running', ?, ?)
            """,
            (
                full_session_id,
                user_id,
                scenario_slug,
                docker_project_name,
                ports_json,
                now.isoformat(),
                expires_at.isoformat(),
            ),
        )
        conn.commit()

    return {
        "id": full_session_id,
        "user_id": user_id,
        "scenario_slug": scenario_slug,
        "docker_project_name": docker_project_name,
        "assigned_ports": assigned_ports,
        "status": "running",
        "started_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "ended_at": None,
    }


def get_active_session(user_id: str, scenario_slug: str) -> Optional[Dict[str, Any]]:
    """Obtiene la sesión activa ('running') más reciente de un estudiante para un escenario."""
    with _get_practice_db_connection() as conn:
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
    """Busca una sesión por su UUID."""
    with _get_practice_db_connection() as conn:
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
    """Actualiza el estado de una sesión."""
    terminal_statuses = {"completed", "stopped", "expired", "error"}
    ended_at = datetime.utcnow().isoformat() if status in terminal_statuses else None

    with _get_practice_db_connection() as conn:
        conn.execute(
            """
            UPDATE practice_sessions 
            SET status = ?, ended_at = COALESCE(?, ended_at)
            WHERE id = ?
            """,
            (status, ended_at, session_id),
        )
        conn.commit()

    return get_session_by_id(session_id)

def get_expired_running_sessions() -> list[Dict[str, Any]]:
    """Obtiene todas las sesiones 'running' cuyo tiempo asignado ya expiró."""
    now_iso = datetime.utcnow().isoformat()
    with _get_practice_db_connection() as conn:
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