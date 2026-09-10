from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any
from .schemas import CheckpointSubmission, SurveySubmission

DB_PATH = "cyberlab.db"


def get_db():
  conn = sqlite3.connect(DB_PATH)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  with get_db() as conn:
    conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoint_progress (
                student_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                checkpoint_id TEXT NOT NULL,
                status TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                completed_at TEXT,
                PRIMARY KEY (student_id, checkpoint_id)
            )
        """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS survey_responses (
                student_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                responses TEXT NOT NULL,
                submitted_at TEXT NOT NULL,
                PRIMARY KEY (student_id, module_id)
            )
        """)
    conn.commit()


def save_checkpoint(submission: CheckpointSubmission) -> dict[str, Any]:
  init_db()
  completed_at = datetime.utcnow().isoformat()
  module_id = getattr(submission, "module_id", "default")
  with get_db() as conn:
    conn.execute(
        """
            INSERT INTO checkpoint_progress (student_id, module_id, checkpoint_id, status, points, completed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, checkpoint_id) DO UPDATE SET
                status = excluded.status,
                points = excluded.points,
                completed_at = excluded.completed_at
        """,
        (
            submission.student_id,
            module_id,
            submission.checkpoint_id,
            submission.status,
            10,
            completed_at,
        ),
    )
    conn.commit()
  return {
      "student_id": submission.student_id,
      "checkpoint_id": submission.checkpoint_id,
      "status": submission.status,
  }


def get_student_dashboard(student_id: str) -> dict[str, Any] | None:
  init_db()
  with get_db() as conn:
    cursor = conn.execute(
        """
            SELECT student_id, module_id, checkpoint_id, status, points, completed_at
            FROM checkpoint_progress
            WHERE student_id = ?
        """,
        (student_id,),
    )
    rows = cursor.fetchall()

  completed_checkpoints = [
      row["checkpoint_id"] for row in rows if row["status"] == "done"
  ]
  total_completed = len(completed_checkpoints)

  return {
      "student_id": student_id,
      "progress_percent": float(total_completed * 10),
      "completed_modules_count": 0,
      "total_modules_count": 10,
      "modules": [dict(r) for r in rows],
  }


def save_survey(submission: SurveySubmission):
  init_db()
  submitted_at = datetime.utcnow().isoformat()
  with get_db() as conn:
    conn.execute(
        """
            INSERT INTO survey_responses (student_id, module_id, responses, submitted_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id, module_id) DO UPDATE SET
                responses = excluded.responses,
                submitted_at = excluded.submitted_at
        """,
        (
            submission.student_id,
            submission.module_id,
            json.dumps(submission.responses),
            submitted_at,
        ),
    )
    conn.commit()