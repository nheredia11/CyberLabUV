from __future__ import annotations

import json
import logging
from typing import Any
from .database import get_db_connection, utcnow
from .schemas import CheckpointSubmission, SurveySubmission
from .content import load_module, load_all_modules, load_catalog

logger = logging.getLogger("cyberlab")


def save_checkpoint(submission: CheckpointSubmission) -> dict[str, Any]:
    now = utcnow()
    module_id = getattr(submission, "module_id", "default")
    user_id = getattr(submission, "user_id", getattr(submission, "student_id", "demo-student"))
    status = getattr(submission, "status", "done")
    evidence = getattr(submission, "evidence", "")

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO checkpoint_submissions (user_id, module_id, checkpoint_id, status, evidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, module_id, checkpoint_id) DO UPDATE SET
                status = excluded.status,
                evidence = excluded.evidence,
                updated_at = excluded.updated_at
            """,
            (user_id, module_id, submission.checkpoint_id, status, evidence, now, now),
        )
        conn.commit()
    return {
        "user_id": user_id,
        "module_id": module_id,
        "checkpoint_id": submission.checkpoint_id,
        "status": status,
    }


def get_student_dashboard(user_id: str) -> dict[str, Any] | None:
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT user_id, module_id, checkpoint_id, status, evidence, updated_at
            FROM checkpoint_submissions
            WHERE user_id = ?
            """,
            (user_id,),
        )
        rows = cursor.fetchall()

    completed_checkpoints = [
        row["checkpoint_id"] for row in rows if row["status"] in ("done", "completed")
    ]
    
    catalog = load_catalog()
    all_modules = load_all_modules()
    total_modules = len(catalog)

    # Calcular progreso total basado en todos los checkpoints reales de todos los módulos
    total_all_checkpoints = sum(len(m.checkpoints) for m in all_modules)
    total_completed = len([r for r in rows if r["status"] in ("done", "completed")])

    progress_percent = 0.0
    if total_all_checkpoints > 0:
        progress_percent = min(100.0, float((total_completed / total_all_checkpoints) * 100))

    return {
        "student_id": user_id,
        "user_id": user_id,
        "progress_percent": progress_percent,
        "completed_modules_count": sum(
            1 for m in all_modules 
            if m.checkpoints and all(cp.id in completed_checkpoints for cp in m.checkpoints)
        ),
        "total_modules_count": total_modules,
        "modules": [dict(r) for r in rows],
    }


def save_survey(submission: SurveySubmission):
    now = utcnow()
    user_id = getattr(submission, "user_id", getattr(submission, "student_id", "demo-student"))
    module_id = submission.module_id
    responses = getattr(submission, "responses", {})
    rating = getattr(submission, "rating", None)
    comments = getattr(submission, "comments", "")

    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO surveys (user_id, module_id, answers_json, rating, comments, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, module_id) DO UPDATE SET
                answers_json = excluded.answers_json,
                rating = excluded.rating,
                comments = excluded.comments
            """,
            (user_id, module_id, json.dumps(responses), rating, comments, now),
        )
        conn.commit()


def get_student_module_progress(user_id: str, module_id: str) -> dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT checkpoint_id, status 
            FROM checkpoint_submissions
            WHERE user_id = ? AND module_id = ?
            """,
            (user_id, module_id)
        )
        rows = cursor.fetchall()

    completed_checkpoints = [row["checkpoint_id"] for row in rows if row["status"] in ("done", "completed")]
    checkpoints_completed = len(completed_checkpoints)
    
    mod = load_module(module_id)
    total_checkpoints = len(mod.checkpoints) if mod and mod.checkpoints else 0

    progress_percent = 0.0
    if total_checkpoints > 0:
        progress_percent = min(100.0, float((checkpoints_completed / total_checkpoints) * 100))
    elif checkpoints_completed > 0:
        progress_percent = min(100.0, float(checkpoints_completed * 25))

    return {
        "user_id": user_id,
        "student_id": user_id,
        "module_id": module_id,
        "progress_percent": progress_percent,
        "checkpoints_completed": checkpoints_completed,
        "total_checkpoints": total_checkpoints,
    }


def get_teacher_analytics() -> dict[str, Any]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) as total FROM checkpoint_submissions")
        total_sub = cursor.fetchone()["total"]
        cursor2 = conn.execute("SELECT * FROM checkpoint_submissions")
        submissions = [dict(r) for r in cursor2.fetchall()]
    return {
        "total_submissions": total_sub,
        "submissions": submissions,
    }