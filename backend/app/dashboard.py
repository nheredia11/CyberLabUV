"""Construcción de la vista de progreso del estudiante (Dashboard y Resultados)."""
from __future__ import annotations

from collections import defaultdict

from .content import load_all_modules
from .database import get_db_connection
from .schemas import DashboardModule, ModuleProgressView, StudentDashboard

DONE_STATUSES = ("done", "completed")


def get_student_progress_state(student_id: str) -> tuple[dict[str, set[str]], set[str]]:
    """Devuelve ({module_id: {checkpoint_id completados}}, {module_id con encuesta})."""
    done: dict[str, set[str]] = defaultdict(set)
    with get_db_connection() as conn:
        for row in conn.execute(
            "SELECT module_id, checkpoint_id FROM checkpoint_submissions "
            "WHERE user_id = ? AND status IN ('done', 'completed')",
            (student_id,),
        ):
            done[row["module_id"]].add(row["checkpoint_id"])
        surveys = {
            row["module_id"]
            for row in conn.execute("SELECT module_id FROM surveys WHERE user_id = ?", (student_id,))
        }
    return done, surveys


def build_student_dashboard(student_id: str) -> StudentDashboard:
    modules = load_all_modules()
    done, surveys = get_student_progress_state(student_id)

    views: list[DashboardModule] = []
    total_cps = done_cps = points = completed_modules = 0

    for module in modules:
        cp_ids = {cp.id for cp in module.checkpoints}
        module_done = done.get(module.id, set()) & cp_ids  # solo checkpoints que existen hoy
        total, completed = len(cp_ids), len(module_done)
        percent = round(completed / total * 100, 1) if total else 0.0

        total_cps += total
        done_cps += completed
        points += sum(cp.points for cp in module.checkpoints if cp.id in module_done)
        if total and completed == total:
            completed_modules += 1

        views.append(
            DashboardModule(
                id=module.id,
                title=module.title,
                description=module.description,
                orden=module.orden,
                progress=ModuleProgressView(
                    percent=percent,
                    completed_checkpoints=completed,
                    total_checkpoints=total,
                    survey_completed=module.id in surveys,
                ),
            )
        )

    return StudentDashboard(
        student_id=student_id,
        general_percent=round(done_cps / total_cps * 100, 1) if total_cps else 0.0,
        completed_modules=completed_modules,
        total_modules=len(modules),
        points=points,
        badges=completed_modules,
        modules=views,
    )
