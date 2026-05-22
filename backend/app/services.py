from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import Any

from .config import get_settings
from .content import load_module, load_modules, scenario_slug_for_module
from .database import connect, dumps, loads, row_to_dict, rows_to_dicts, utcnow


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with connect() as conn:
        return row_to_dict(conn.execute("SELECT id, name, email, role, avatar FROM users WHERE email = ?", (email,)).fetchone())

def list_users(role: str | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if role:
            rows = conn.execute("SELECT id, name, email, role, avatar FROM users WHERE role = ? ORDER BY name", (role,)).fetchall()
        else:
            rows = conn.execute("SELECT id, name, email, role, avatar FROM users ORDER BY role, name").fetchall()
        return rows_to_dicts(rows)

def module_progress(user_id: str, module_id: str) -> dict[str, Any]:
    module = load_module(module_id)
    checkpoints = module.get("checkpoints", [])
    total = len(checkpoints)
    with connect() as conn:
        rows = conn.execute(
            "SELECT checkpoint_id, status, evidence, updated_at FROM checkpoint_submissions WHERE user_id = ? AND module_id = ?",
            (user_id, module_id),
        ).fetchall()
        survey_count = conn.execute(
            "SELECT COUNT(*) AS c FROM surveys WHERE user_id = ? AND module_id = ?",
            (user_id, module_id),
        ).fetchone()["c"]
    by_checkpoint = {r["checkpoint_id"]: dict(r) for r in rows}
    completed = sum(1 for cp in checkpoints if by_checkpoint.get(cp["id"], {}).get("status") == "done")
    percent = round((completed / total) * 100) if total else 0
    return {
        "module_id": module_id,
        "completed_checkpoints": completed,
        "total_checkpoints": total,
        "percent": percent,
        "survey_completed": survey_count > 0,
        "checkpoints": [{**cp, "submission": by_checkpoint.get(cp["id"])} for cp in checkpoints],
    }

def dashboard(user_id: str = "ana") -> dict[str, Any]:
    modules = load_modules()
    progress = [module_progress(user_id, m["id"]) for m in modules]
    total_cp = sum(p["total_checkpoints"] for p in progress)
    done_cp = sum(p["completed_checkpoints"] for p in progress)
    general = round((done_cp / total_cp) * 100) if total_cp else 0
    latest = next((m for m, p in zip(modules, progress) if p["percent"] < 100), modules[-1] if modules else None)
    return {
        "general_percent": general,
        "completed_modules": sum(1 for p in progress if p["percent"] == 100),
        "total_modules": len(modules),
        "badges": max(1, sum(1 for p in progress if p["percent"] >= 50)),
        "points": 1250 + done_cp * 50,
        "current_module": latest,
        "modules": [{**m, "progress": p} for m, p in zip(modules, progress)],
    }

def save_checkpoint(module_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    now = utcnow()
    with connect() as conn:
        conn.execute(
            """INSERT INTO checkpoint_submissions(user_id, module_id, checkpoint_id, status, evidence, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, module_id, checkpoint_id) DO UPDATE SET
                 status = excluded.status, evidence = excluded.evidence, updated_at = excluded.updated_at""",
            (payload["user_id"], module_id, payload["checkpoint_id"], payload["status"], payload.get("evidence"), now, now),
        )
    return module_progress(payload["user_id"], module_id)

def save_survey(module_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            "INSERT INTO surveys(user_id, module_id, answers_json, rating, comments, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (payload["user_id"], module_id, dumps(payload["answers"]), payload.get("rating"), payload.get("comments"), utcnow()),
        )
    return {"saved": True, "progress": module_progress(payload["user_id"], module_id)}

def save_note(payload: dict[str, Any]) -> dict[str, Any]:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO notes(teacher_id, student_id, module_id, body, created_at) VALUES (?, ?, ?, ?, ?)",
            (payload["teacher_id"], payload["student_id"], payload["module_id"], payload["body"], utcnow()),
        )
    return {"id": cur.lastrowid, **payload}

def analytics() -> dict[str, Any]:
    students = list_users("student")
    modules = load_modules()
    module_rows = []
    for module in modules:
        progresses = [module_progress(student["id"], module["id"]) for student in students]
        avg = round(sum(p["percent"] for p in progresses) / len(progresses)) if progresses else 0
        module_rows.append({"module_id": module["id"], "title": module["titulo"], "avg_progress": avg})
    with connect() as conn:
        surveys = rows_to_dicts(conn.execute("SELECT module_id, rating, comments, created_at FROM surveys ORDER BY created_at DESC LIMIT 20").fetchall())
        attempts = rows_to_dicts(conn.execute("SELECT scenario_id, action, status, created_at FROM scenario_events ORDER BY created_at DESC LIMIT 20").fetchall())
    return {"students": students, "modules": module_rows, "surveys": surveys, "scenario_events": attempts}

def run_scenario_action(user_id: str, scenario_id: str, action: str) -> dict[str, Any]:
    settings = get_settings()
    allowed = {"recon", "auth_http", "webapp", "smoke"}
    if scenario_id not in allowed:
        status, message = "error", f"Escenario no permitido: {scenario_id}"
    elif not settings.allow_scenario_commands:
        status = "dry-run"
        message = "Comando registrado en modo seguro. Para ejecutar Docker define ALLOW_SCENARIO_COMMANDS=true."
    else:
        script = {"start": "run-scenario.sh", "stop": "stop-scenario.sh", "reset": "reset.sh", "status": "status-scenarios.sh"}.get(action)
        try:
            if action == "reset" and scenario_id != "smoke":
                subprocess.run(["bash", str(settings.project_root / "scripts" / "stop-scenario.sh"), scenario_id], check=False, capture_output=True, text=True, timeout=60)
                cmd = ["bash", str(settings.project_root / "scripts" / "run-scenario.sh"), scenario_id]
            elif action in {"start", "stop"}:
                cmd = ["bash", str(settings.project_root / "scripts" / script), scenario_id]
            else:
                cmd = ["bash", str(settings.project_root / "scripts" / script)]
            completed = subprocess.run(cmd, cwd=settings.project_root, capture_output=True, text=True, timeout=90)
            status = "ok" if completed.returncode == 0 else "error"
            message = (completed.stdout or completed.stderr).strip()[-1200:]
        except Exception as exc:  # pragma: no cover
            status, message = "error", str(exc)
    with connect() as conn:
        conn.execute(
            "INSERT INTO scenario_events(user_id, scenario_id, action, status, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, scenario_id, action, status, message, utcnow()),
        )
    return {"scenario_id": scenario_id, "action": action, "status": status, "message": message}
