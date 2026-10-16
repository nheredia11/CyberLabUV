from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Ruta de la base de datos (compatible con monkeypatch en tests)
DATABASE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "cyberlabuv.sqlite3"

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def connect():
    """Función de compatibilidad que redirige a get_db_connection para servicios antiguos."""
    return get_db_connection()

def get_db_connection():
    """Conexión a la base de datos SQLite sin llamadas circulares."""
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa todas las tablas de la base de datos de forma idempotente."""
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS checkpoint_submissions (
                user_id TEXT,
                module_id TEXT,
                checkpoint_id TEXT,
                status TEXT,
                evidence TEXT,
                created_at TEXT,
                updated_at TEXT,
                PRIMARY KEY (user_id, module_id, checkpoint_id)
            );

            CREATE TABLE IF NOT EXISTS surveys (
                user_id TEXT,
                module_id TEXT,
                answers_json TEXT,
                rating INTEGER,
                comments TEXT,
                created_at TEXT,
                PRIMARY KEY (user_id, module_id)
            );

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT UNIQUE,
                role TEXT,
                avatar TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT,
                student_id TEXT,
                module_id TEXT,
                body TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS consents (
                user_id TEXT PRIMARY KEY,
                accepted_at TEXT,
                version TEXT
            );

            CREATE TABLE IF NOT EXISTS practice_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                scenario_id TEXT,
                docker_project_name TEXT,
                assigned_ports TEXT,
                status TEXT,
                created_at TEXT
            );
        """)
        conn.commit()
        
def get_active_session(user_id: str, scenario_id: str) -> dict[str, Any] | None:
    """Alias o wrapper para obtener la sesión activa de un escenario."""
    return get_practice_session(user_id, scenario_id)

# Helpers de sesiones requeridos por el scenario_runner
def create_practice_session(user_id: str, scenario_id: str, session_id: str, docker_project_name: str, assigned_ports: Any) -> dict[str, Any]:
    init_db()
    now = utcnow()
    ports_str = json.dumps(assigned_ports) if isinstance(assigned_ports, (dict, list)) else str(assigned_ports)
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO practice_sessions (session_id, user_id, scenario_id, docker_project_name, assigned_ports, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'running', ?)
            """,
            (session_id, user_id, scenario_id, docker_project_name, ports_str, now)
        )
        conn.commit()
    return {"session_id": session_id, "user_id": user_id, "scenario_id": scenario_id}

def get_practice_session(user_id: str, scenario_id: str) -> dict[str, Any] | None:
    init_db()
    with get_db_connection() as conn:
        row = conn.execute(
            """
            SELECT session_id, user_id, scenario_id, docker_project_name, assigned_ports, status, created_at 
            FROM practice_sessions 
            WHERE user_id = ? AND scenario_id = ? AND status = 'running'
            ORDER BY created_at DESC LIMIT 1
            """,
            (user_id, scenario_id)
        ).fetchone()
        if not row:
            return None
        res = dict(row)
        try:
            res["assigned_ports"] = json.loads(res["assigned_ports"])
        except Exception:
            pass
        return res

def close_practice_session(user_id: str, scenario_id: str) -> bool:
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE practice_sessions SET status = 'stopped' 
            WHERE user_id = ? AND scenario_id = ? AND status = 'running'
            """,
            (user_id, scenario_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    
def update_session_status(*args, **kwargs):
    """Actualiza el estado de una sesión de práctica de forma flexible (por session_id o user_id/scenario_id)."""
    init_db()
    with get_db_connection() as conn:
        if len(args) == 2:
            session_id, status = args
            cursor = conn.execute("UPDATE practice_sessions SET status = ? WHERE session_id = ?", (status, session_id))
        elif len(args) == 3:
            user_id, scenario_id, status = args
            cursor = conn.execute("UPDATE practice_sessions SET status = ? WHERE user_id = ? AND scenario_id = ?", (status, user_id, scenario_id))
        elif "session_id" in kwargs and "status" in kwargs:
            cursor = conn.execute("UPDATE practice_sessions SET status = ? WHERE session_id = ?", (kwargs["status"], kwargs["session_id"]))
        elif "user_id" in kwargs and "scenario_id" in kwargs and "status" in kwargs:
            cursor = conn.execute("UPDATE practice_sessions SET status = ? WHERE user_id = ? AND scenario_id = ?", (kwargs["status"], kwargs["user_id"], kwargs["scenario_id"]))
        else:
            return False
        conn.commit()
        return cursor.rowcount > 0
    
def get_expired_running_sessions() -> list[dict[str, Any]]:
    """Devuelve las sesiones de práctica que se encuentran en estado 'running' para su limpieza."""
    init_db()
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT session_id, user_id, scenario_id, docker_project_name, assigned_ports, status, created_at 
            FROM practice_sessions 
            WHERE status = 'running'
            """
        ).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            try:
                item["assigned_ports"] = json.loads(item["assigned_ports"])
            except Exception:
                pass
            results.append(item)
        return results

def dumps(obj: Any) -> str:
    return json.dumps(obj)

def row_to_dict(row) -> dict[str, Any] | None:
    return dict(row) if row else None

def rows_to_dicts(rows) -> list[dict[str, Any]]:
    return [dict(r) for r in rows]