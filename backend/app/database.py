from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import os

DEFAULT_DB_PATH = os.environ.get("CYBERLAB_DB", "data/cyberlabuv.sqlite3")

def get_db_path() -> Path:
    path = Path(DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def connect():
    return get_db_connection()

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def init_db():
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoint_submissions (
                user_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                checkpoint_id TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT,
                PRIMARY KEY (user_id, module_id, checkpoint_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                user_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                rating INTEGER,
                comments TEXT DEFAULT '',
                created_at TEXT,
                PRIMARY KEY (user_id, module_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scenario_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                status TEXT NOT NULL,
                local_url TEXT,
                docker_project_name TEXT,
                assigned_ports TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()

def create_practice_session(
    user_id: str,
    scenario_id: str = "",
    scenario_slug: str = "",
    session_id: str = "sess-default",
    local_url: str = "",
    docker_project_name: str = "",
    assigned_ports: Any = "",
    duration_minutes: int = 90
):
    init_db()
    now = utcnow()
    scen = scenario_id or scenario_slug
    ports_str = json.dumps(assigned_ports) if isinstance(assigned_ports, dict) else str(assigned_ports)
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO scenario_sessions (session_id, user_id, scenario_id, status, local_url, docker_project_name, assigned_ports, created_at, updated_at)
            VALUES (?, ?, ?, 'running', ?, ?, ?, ?, ?)
            """,
            (session_id, user_id, scen, local_url, docker_project_name, ports_str, now, now)
        )
        conn.commit()
    return {"id": session_id, "session_id": session_id, "status": "running"}


def get_active_session(user_id: str, scenario_id: str):
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM scenario_sessions WHERE user_id = ? AND scenario_id = ? AND status = 'running'",
            (user_id, scenario_id)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_expired_running_sessions(max_age_seconds: int = 3600):
    init_db()
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM scenario_sessions WHERE status = 'running'"
        )
        return [dict(row) for row in cursor.fetchall()]

def update_session_status(session_id: str, status: str):
    init_db()
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE scenario_sessions SET status = ?, updated_at = ? WHERE session_id = ?",
            (status, utcnow(), session_id)
        )
        conn.commit()