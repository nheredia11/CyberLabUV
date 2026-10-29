from __future__ import annotations

import json
import logging
from typing import Any
from .database import get_db_connection, utcnow, init_db
from .schemas import CheckpointSubmission, SurveySubmission
from .content import load_module, load_all_modules, load_catalog

logger = logging.getLogger("cyberlab")


def save_checkpoint(submission: CheckpointSubmission) -> dict[str, Any]:
    module_id = getattr(submission, "module_id", "default")
    
    # 🛡️ Validación estricta para integridad de tesis (Bloque 2)
    mod = load_module(module_id)
    if not mod:
        raise ValueError(f"Módulo no encontrado: {module_id}")
    
    valid_cp_ids = {cp.id for cp in (mod.checkpoints or [])}
    if submission.checkpoint_id not in valid_cp_ids:
        raise ValueError(f"Checkpoint inválido '{submission.checkpoint_id}' para el módulo {module_id}")

    now = utcnow()
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
    
def save_note(payload: dict[str, Any]) -> dict[str, Any]:
    init_db()
    now = utcnow()
    teacher_id = payload.get("teacher_id")
    student_id = payload.get("student_id")
    module_id = payload.get("module_id", "general")
    body = payload.get("body", "")
    
    with get_db_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO notes (teacher_id, student_id, module_id, body, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (teacher_id, student_id, module_id, body, now)
        )
        conn.commit()
        note_id = cur.lastrowid
        
    return {"id": note_id, **payload, "created_at": now}


def save_consent(user_id: str, version: str = "1.0") -> dict[str, Any]:
    init_db()
    now = utcnow()
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO consents (user_id, accepted_at, version)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                accepted_at = excluded.accepted_at,
                version = excluded.version
            """,
            (user_id, now, version)
        )
        conn.commit()
    return {"user_id": user_id, "accepted": True, "accepted_at": now}

def get_consent(user_id: str) -> dict[str, Any] | None:
    init_db()
    with get_db_connection() as conn:
        row = conn.execute("SELECT user_id, accepted_at, version FROM consents WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    
def get_pilot_export_data() -> list[dict[str, Any]]:
    """Extrae datos consolidados de checkpoints y encuestas para el análisis estadístico del piloto."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                cs.user_id,
                cs.module_id,
                cs.checkpoint_id,
                cs.status as checkpoint_status,
                cs.evidence,
                cs.updated_at,
                s.rating,
                s.comments,
                s.answers_json
            FROM checkpoint_submissions cs
            LEFT JOIN surveys s ON cs.user_id = s.user_id AND cs.module_id = s.module_id
        """)
        return [dict(row) for row in cursor.fetchall()]