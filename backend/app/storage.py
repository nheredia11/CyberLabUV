import sqlite3
import datetime
from typing import List, Dict, Any, Optional

try:
    from app.schemas import (
        CheckpointSubmission,
        CheckpointProgressRecord,
        StudentDashboard,
        TeacherAnalytics,
        SurveySubmission,
        StudentModuleProgress,
    )
except ImportError:
    from .schemas import (
        CheckpointSubmission,
        CheckpointProgressRecord,
        StudentDashboard,
        TeacherAnalytics,
        SurveySubmission,
        StudentModuleProgress,
    )

DB_PATH = "cyberlab.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoint_progress (
                user_id TEXT,
                module_id TEXT,
                checkpoint_id TEXT,
                status TEXT,
                evidence TEXT,
                completed INTEGER,
                updated_at TEXT,
                PRIMARY KEY (user_id, module_id, checkpoint_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scenario_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id TEXT,
                action TEXT,
                returncode INTEGER,
                stdout TEXT,
                stderr TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                module_id TEXT,
                responses TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

init_db()

def save_scenario_event(scenario_id: str, action: str, returncode: int, stdout: str, stderr: str):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO scenario_events (scenario_id, action, returncode, stdout, stderr, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (scenario_id, action, returncode, stdout, stderr, now))
        conn.commit()

def save_checkpoint(student_id: str, module_id: str, checkpoint_id: str, evidence: str, status: str) -> None:
    is_completed = 1 if status == "done" else 0
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO checkpoint_progress (student_id, module_id, checkpoint_id, evidence, status, completed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id, module_id, checkpoint_id) 
            DO UPDATE SET evidence=excluded.evidence, status=excluded.status, completed=excluded.completed;
            """,
            (student_id, module_id, checkpoint_id, evidence, status, is_completed),
        )
        conn.commit()

def save_survey(survey: SurveySubmission) -> Dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO surveys (user_id, module_id, responses, created_at)
            VALUES (?, ?, ?, ?)
        """, (survey.user_id, survey.module_id, str(survey.responses), now))
        conn.commit()
    return {"status": "success", "message": "Encuesta guardada correctamente."}

def get_student_module_progress(student_id: str, module_id: str) -> StudentModuleProgress:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT checkpoint_id, status, evidence, completed, updated_at
            FROM checkpoint_progress
            WHERE user_id = ? AND module_id = ?
        """, (student_id, module_id))
        rows = cursor.fetchall()
        checkpoints = [dict(row) for row in rows]
        is_completed = len(checkpoints) > 0 and all(r.get("completed") == 1 for r in checkpoints)

        return StudentModuleProgress(
            user_id=student_id,
            module_id=module_id,
            checkpoints=checkpoints,
            completed=is_completed
        )

def get_student_dashboard(student_id: str) -> StudentDashboard:
    # Retorna la estructura garantizando la llave canónica progress_percent
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(DISTINCT checkpoint_id) FROM checkpoint_progress WHERE student_id = ? AND completed = 1",
            (student_id,),
        )
        completed_count = cursor.fetchone()[0] or 0

    total_checkpoints = 10  # Valor base configurable
    calculated_percent = round((completed_count / total_checkpoints) * 100, 2) if total_checkpoints > 0 else 0.0

    return StudentDashboard(
        student_id=student_id,
        progress_percent=calculated_percent,
        completed_modules_count=0,
        total_modules_count=5,
        modules=[],
    )

def get_teacher_analytics() -> TeacherAnalytics:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, COUNT(DISTINCT checkpoint_id) as total_completed
            FROM checkpoint_progress
            WHERE completed = 1 OR status = 'completed'
            GROUP BY user_id
        """)
        rows = cursor.fetchall()
        students_list = [dict(row) for row in rows]

        return TeacherAnalytics(
            total_students=len(students_list),
            active_labs=5,
            students=students_list
        )