from __future__ import annotations

import re
import subprocess
from typing import Any
import hashlib
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .config import get_settings
from .content import load_module, load_modules
from .database import connect, dumps, row_to_dict, rows_to_dicts, utcnow


def get_user_by_email(email: str) -> dict[str, Any] | None:
    with connect() as conn:
        return row_to_dict(conn.execute("SELECT id, name, email, role, avatar FROM users WHERE email = ?", (email,)).fetchone())
    
def get_or_create_google_user(credential: str) -> dict[str, Any]:
    settings = get_settings()

    if not settings.google_client_id:
        raise ValueError("GOOGLE_CLIENT_ID no está configurado en el backend.")

    
    google_payload = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        settings.google_client_id,
        clock_skew_in_seconds=30,
    )

    email = (google_payload.get("email") or "").lower().strip()
    name = google_payload.get("name") or email.split("@")[0]
    picture = google_payload.get("picture")
    email_verified = google_payload.get("email_verified", False)

    if not email:
        raise PermissionError("La cuenta de Google no tiene correo asociado.")

    if not email_verified:
        raise PermissionError("El correo de Google no aparece como verificado.")

    domain = email.split("@")[-1].lower().strip()
    allowed_domains = [d.lower().strip() for d in settings.google_allowed_domains]

    if domain not in allowed_domains:
        allowed = ", ".join(allowed_domains)
        raise PermissionError(
            f"Solo se permiten cuentas institucionales. "
            f"Correo recibido: {email}. "
            f"Dominio recibido: {domain}. "
            f"Dominios permitidos: {allowed}"
        )

    user_id = hashlib.sha1(email.encode("utf-8")).hexdigest()[:12]
    avatar = "".join([part[0] for part in name.split()[:2]]).upper() or "UV"

    # Si ya existe por ID, lo retornamos.
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, email, role, avatar FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()

        if row:
            user = dict(row)
            user["picture"] = picture
            return user

        # Si ya existe por email, también lo retornamos.
        row = conn.execute(
            "SELECT id, name, email, role, avatar FROM users WHERE lower(email) = lower(?)",
            (email,),
        ).fetchone()

        if row:
            user = dict(row)
            user["picture"] = picture
            return user

        # Para demo: si el correo contiene profesor/docente lo marcamos docente.
        role = "teacher" if any(
            marker in email for marker in ["prof", "docente", "teacher"]
        ) else "student"

        conn.execute(
            """
            INSERT INTO users(id, name, email, role, avatar, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, name, email, role, avatar, utcnow()),
        )

    return {
        "id": user_id,
        "name": name,
        "email": email,
        "role": role,
        "avatar": avatar,
        "picture": picture,
    }

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


def _learning_level(percent: int) -> str:
    if percent >= 85:
        return "Autónomo"
    if percent >= 55:
        return "En consolidación"
    if percent >= 25:
        return "Inicial"
    return "Pendiente"


def adaptive_feedback(user_id: str, module_id: str) -> dict[str, Any]:
    module = load_module(module_id)
    progress = module_progress(user_id, module_id)
    missing = [cp for cp in progress["checkpoints"] if not cp.get("submission") or cp["submission"].get("status") != "done"]
    percent = progress["percent"]
    if percent >= 85:
        message = "Excelente avance. Ya puedes concentrarte en explicar el procedimiento, justificar hallazgos y proponer mitigaciones."
        next_actions = ["Redacta un reporte técnico corto", "Incluye capturas o logs como evidencia", "Relaciona el escenario con MITRE ATT&CK, OWASP o NIST"]
    elif percent >= 55:
        message = "Vas bien, pero todavía falta cerrar evidencias. La prioridad es completar checkpoints y documentar comandos usados."
        next_actions = ["Completa los checkpoints pendientes", "Guarda el resultado de la terminal guiada", "Revisa la teoría antes de repetir el laboratorio"]
    else:
        message = "Conviene reforzar la ruta teórica antes de ejecutar el laboratorio. Avanza paso a paso y registra evidencia mínima."
        next_actions = ["Lee los objetivos del módulo", "Ejecuta primero el comando sugerido", "Pide retroalimentación docente si te bloqueas"]
    return {
        "module_id": module_id,
        "title": module["titulo"],
        "level": _learning_level(percent),
        "progress_percent": percent,
        "message": message,
        "missing_checkpoints": [cp["titulo"] for cp in missing],
        "next_actions": next_actions,
        "teacher_hint": f"Revisar a estudiantes con nivel '{_learning_level(percent)}' en {module['titulo']} y comparar evidencia contra checkpoints.",
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
        "modules": [{**m, "progress": p, "feedback": adaptive_feedback(user_id, m["id"])} for m, p in zip(modules, progress)],
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
    return {"saved": True, "progress": module_progress(payload["user_id"], module_id), "feedback": adaptive_feedback(payload["user_id"], module_id)}


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
    at_risk = 0
    total_progress = 0
    for module in modules:
        progresses = [module_progress(student["id"], module["id"]) for student in students]
        avg = round(sum(p["percent"] for p in progresses) / len(progresses)) if progresses else 0
        total_progress += avg
        at_risk += sum(1 for p in progresses if p["percent"] < 50)
        module_rows.append({"module_id": module["id"], "title": module["titulo"], "avg_progress": avg, "level": _learning_level(avg)})
    with connect() as conn:
        surveys = rows_to_dicts(conn.execute("SELECT module_id, rating, comments, created_at FROM surveys ORDER BY created_at DESC LIMIT 20").fetchall())
        attempts = rows_to_dicts(conn.execute("SELECT scenario_id, action, status, created_at FROM scenario_events ORDER BY created_at DESC LIMIT 20").fetchall())
        terminal = rows_to_dicts(conn.execute("SELECT scenario_id, command, status, created_at FROM terminal_commands ORDER BY created_at DESC LIMIT 20").fetchall())
        done = conn.execute("SELECT COUNT(*) AS c FROM checkpoint_submissions WHERE status = 'done'").fetchone()["c"]
    avg_course = round(total_progress / len(module_rows)) if module_rows else 0
    return {
        "students": students,
        "modules": module_rows,
        "surveys": surveys,
        "scenario_events": attempts,
        "terminal_events": terminal,
        "kpis": {
            "avg_course_progress": avg_course,
            "students_at_risk": at_risk,
            "completed_checkpoints": done,
            "survey_count": len(surveys),
            "terminal_commands": len(terminal),
        },
        "recommendations": [
            "Usar los estudiantes en riesgo para tutorías cortas por módulo.",
            "Pedir evidencia mínima: comando, resultado y explicación del hallazgo.",
            "Comparar tiempo de ejecución, checkpoints y encuesta para validar utilidad pedagógica.",
        ],
    }


SAFE_COMMANDS: dict[str, dict[str, str]] = {
    "recon": {
        "nmap -sV 10.10.10.20": "Starting Nmap...\nPORT   STATE SERVICE VERSION\n22/tcp open  ssh     OpenSSH 8.9\n80/tcp open  http    nginx 1.22\nConclusión: hay servicios SSH y HTTP disponibles para análisis controlado.",
        "curl http://localhost:8081": "HTTP/1.1 200 OK\n<title>Recon Lab</title>\nMensaje: servicio web objetivo activo.",
    },
    "auth_http": {
        "curl -i http://localhost:8082/login": "HTTP/1.1 200 OK\nFormulario de autenticación disponible. Objetivo: analizar credenciales débiles en ambiente controlado.",
        "hydra -l student -P wordlists/demo.txt localhost http-post-form": "[SIMULADO] Credencial encontrada: student / cyberlab123\nEvidencia: ataque de fuerza bruta limitado en laboratorio local.",
    },
    "webapp": {
        "curl 'http://localhost:8083/search?q=test'": "HTTP/1.1 200 OK\nBúsqueda ejecutada. Revisa si la entrada es sanitizada antes de continuar.",
        "curl 'http://localhost:8083/item?id=1'": "HTTP/1.1 200 OK\nItem 1 encontrado. Siguiente paso: probar controles de validación de parámetros.",
    },
}


def _normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def simulate_terminal_command(user_id: str, scenario_id: str, command: str) -> dict[str, Any]:
    normalized = _normalize_command(command)
    scenario_commands = SAFE_COMMANDS.get(scenario_id, {})
    if normalized in scenario_commands:
        status = "ok"
        output = scenario_commands[normalized]
    else:
        status = "blocked"
        output = "Comando no permitido en la terminal guiada. Usa un comando sugerido para mantener el laboratorio seguro y reproducible."
    with connect() as conn:
        conn.execute(
            "INSERT INTO terminal_commands(user_id, scenario_id, command, status, output, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, scenario_id, normalized, status, output, utcnow()),
        )
    return {
        "scenario_id": scenario_id,
        "command": normalized,
        "status": status,
        "output": output,
        "suggested_commands": list(scenario_commands.keys()),
    }


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
