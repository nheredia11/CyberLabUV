from __future__ import annotations

import json
import sqlite3
import uuid
import os
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterator, Dict, Optional

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

-- NUEVA TABLA: Sesiones de Práctica aisladas en Docker
CREATE TABLE IF NOT EXISTS practice_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    scenario_slug TEXT NOT NULL,
    docker_project_name TEXT UNIQUE NOT NULL,
    assigned_ports TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'starting',
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    ended_at TEXT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_scenario 
ON practice_sessions(user_id, scenario_slug);

CREATE INDEX IF NOT EXISTS idx_sessions_status_expires 
ON practice_sessions(status, expires_at);
"""

DEFAULT_USERS = [
    {"id": "ana", "name": "Ana Rodríguez", "email": "ana.rodriguez@uv.edu.co", "role": "student", "avatar": "AR"},
    {"id": "carlos", "name": "Prof. Carlos M.", "email": "carlos.m@uv.edu.co", "role": "teacher", "avatar": "CM"},
]

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def get_db_connection() -> Iterator[sqlite3.Connection]:
    """Abre y retorna una conexión a SQLite asegurando que el directorio exista."""
    # Obtenemos la ruta de la base de datos (es un string por defecto)
    db_path = get_settings().database_path
    
    # Garantizamos que el directorio padre exista antes de la conexión
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path, timeout=15.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

# Alias por retrocompatibilidad con importaciones previas
connect = get_db_connection

def init_db() -> None:
    with get_db_connection() as conn:
        conn.executescript(SCHEMA)
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

# ============================================================
# PRACTICE SESSIONS - Aislamiento de escenarios Docker
# ============================================================

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
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=duration_minutes)
    ports_json = dumps(assigned_ports)

    with get_db_connection() as conn:
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
    with get_db_connection() as conn:
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
        session_dict["assigned_ports"] = loads(session_dict["assigned_ports"])
        return session_dict

def get_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    """Busca una sesión por su UUID."""
    with get_db_connection() as conn:
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
        session_dict["assigned_ports"] = loads(session_dict["assigned_ports"])
        return session_dict

def update_session_status(session_id: str, new_status: str) -> None:
    """Actualiza el estado de una sesión en la base de datos."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE practice_sessions SET status = ? WHERE id = ?",
            (new_status, session_id)
        )
        conn.commit()

def get_expired_running_sessions() -> list[dict]:
    """Obtiene todas las sesiones con estado 'running' cuya fecha de expiración ha pasado."""
    now_iso = datetime.now(timezone.utc).isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, scenario_slug, docker_project_name, status, expires_at
            FROM practice_sessions
            WHERE status = 'running' AND expires_at <= ?
            """,
            (now_iso,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
