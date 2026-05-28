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
