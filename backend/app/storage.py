from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .config import get_settings
from .content import load_all_modules
from .schemas import (
    CheckpointProgressRecord,
    CheckpointSubmission,
    StudentDashboard,
    StudentModuleProgress,
    SurveySubmission,
    TeacherAnalytics,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    db_path = settings.absolute_database_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS checkpoint_progress (
                student_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                checkpoint_id TEXT NOT NULL,
                evidence TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (student_id, module_id, checkpoint_id)
            );

            CREATE TABLE IF NOT EXISTS survey_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                module_id TEXT NOT NULL,
                answers_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS scenario_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT NOT NULL,
                action TEXT NOT NULL,
                returncode INTEGER,
                stdout TEXT NOT NULL DEFAULT '',
                stderr TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )


def save_checkpoint(submission: CheckpointSubmission) -> None:
    is_completed = 1 if submission.status == "completed" else 0
    
    with get_connection() as conn:  # Corregido: get_connection en lugar de get_db_connection
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(checkpoint_progress)")
        columns = [row["name"] for row in cursor.fetchall()]
        
        if "status" in columns and "feedback" in columns:
            cursor.execute(
                """
                INSERT INTO checkpoint_progress 
                (student_id, module_id, checkpoint_id, evidence, completed, status, feedback, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, module_id, checkpoint_id) 
                DO UPDATE SET 
                    evidence = excluded.evidence,
                    completed = excluded.completed,
                    status = excluded.status,
                    feedback = excluded.feedback,
                    updated_at = excluded.updated_at
                """,
                (
                    submission.student_id,
                    submission.module_id,
                    submission.checkpoint_id,
                    submission.evidence,
                    is_completed,
                    submission.status,
                    submission.feedback,
                    utc_now_iso(),
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO checkpoint_progress 
                (student_id, module_id, checkpoint_id, evidence, completed, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(student_id, module_id, checkpoint_id) 
                DO UPDATE SET 
                    evidence = excluded.evidence,
                    completed = excluded.completed,
                    updated_at = excluded.updated_at
                """,
                (
                    submission.student_id,
                    submission.module_id,
                    submission.checkpoint_id,
                    submission.evidence,
                    is_completed,
                    utc_now_iso(),
                ),
            )
        conn.commit()


def save_survey(submission: SurveySubmission) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO survey_responses (student_id, module_id, answers_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                submission.student_id,
                submission.module_id.upper(),
                json.dumps(submission.answers, ensure_ascii=False),
                utc_now_iso(),
            ),
        )


def save_scenario_event(scenario_id: str, action: str, returncode: int | None, stdout: str, stderr: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scenario_events (scenario_id, action, returncode, stdout, stderr, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (scenario_id, action, returncode, stdout[-4000:], stderr[-4000:], utc_now_iso()),
        )


def get_student_dashboard(student_id: str) -> StudentDashboard:
    modules = load_all_modules()
    checkpoints_total = sum(len(module.checkpoints) for module in modules)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT module_id, checkpoint_id
            FROM checkpoint_progress
            WHERE student_id = ? AND completed = 1
            """,
            (student_id,),
        ).fetchall()

    completed_pairs = {(row["module_id"], row["checkpoint_id"]) for row in rows}
    started_modules = {module_id for module_id, _ in completed_pairs}
    completed = len(completed_pairs)
    progress = round((completed / checkpoints_total) * 100, 2) if checkpoints_total else 0.0

    return StudentDashboard(
        student_id=student_id,
        modules_total=len(modules),
        modules_started=len(started_modules),
        checkpoints_completed=completed,
        general_percent=progress,
        modules=modules,
    )


def get_teacher_analytics() -> TeacherAnalytics:
    modules = load_all_modules()
    checkpoints_total = sum(len(module.checkpoints) for module in modules)

    with get_connection() as conn:
        students_total = conn.execute(
            "SELECT COUNT(DISTINCT student_id) AS total FROM checkpoint_progress"
        ).fetchone()["total"]
        checkpoints_completed = conn.execute(
            "SELECT COUNT(*) AS total FROM checkpoint_progress WHERE completed = 1"
        ).fetchone()["total"]

    denominator = max(students_total * checkpoints_total, 1)
    average = round((checkpoints_completed / denominator) * 100, 2)

    return TeacherAnalytics(
        modules_total=len(modules),
        students_total=students_total,
        checkpoints_completed=checkpoints_completed,
        checkpoints_total=checkpoints_total * max(students_total, 1),
        average_progress_percent=average,
        updated_at=datetime.now(timezone.utc),
    )
    
def get_student_module_progress(student_id: str, module_id: str) -> StudentModuleProgress:
    module_id = module_id.upper()
    modules = {module.id: module for module in load_all_modules()}

    if module_id not in modules:
        raise ValueError(f"No existe el módulo {module_id}")

    module = modules[module_id]
    checkpoints_total = len(module.checkpoints)

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT student_id, module_id, checkpoint_id, evidence, completed, updated_at
            FROM checkpoint_progress
            WHERE student_id = ? AND module_id = ?
            ORDER BY updated_at DESC
            """,
            (student_id, module_id),
        ).fetchall()

    records = [
        CheckpointProgressRecord(
            student_id=row["student_id"],
            module_id=row["module_id"],
            checkpoint_id=row["checkpoint_id"],
            evidence=row["evidence"],
            completed=bool(row["completed"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
        for row in rows
    ]

    checkpoints_completed = sum(1 for item in records if item.completed)
    progress = round((checkpoints_completed / checkpoints_total) * 100, 2) if checkpoints_total else 0.0

    return StudentModuleProgress(
        student_id=student_id,
        module_id=module_id,
        checkpoints_completed=checkpoints_completed,
        checkpoints_total=checkpoints_total,
        progress_percent=progress,
        checkpoints=records,
    )
    
    