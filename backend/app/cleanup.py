import asyncio
import logging
import os
from pathlib import Path

from .config import get_settings
from .database import get_expired_running_sessions, update_session_status
from .scenario_runner import SCENARIOS, _run_cmd_async

logger = logging.getLogger("cyberlabuv.cleanup")


async def cleanup_expired_sessions() -> int:
    """Busca sesiones expiradas, ejecuta 'docker compose down' y actualiza su estado a 'expired'."""
    expired_sessions = get_expired_running_sessions()
    cleaned_count = 0

    for session in expired_sessions:
        session_id = session["id"]
        project_name = session["docker_project_name"]
        slug = session["scenario_slug"]

        logger.info(f"[CLEANUP] Procesando sesión expirada: {session_id} ({slug})")

        scenario = next((s for s in SCENARIOS.values() if s.slug == slug), None)
        if not scenario:
            logger.error(f"[CLEANUP] No se encontró escenario para el slug: {slug}")
            update_session_status(session_id, "expired")
            continue

        compose_path = get_settings().root_dir / scenario.compose_file
        cmd = [
            "docker", "compose",
            "-p", project_name,
            "-f", str(compose_path),
            "down", "-v", "--remove-orphans"
        ]

        returncode, _, stderr = await _run_cmd_async(
            cmd,
            cwd=get_settings().root_dir,
            env=os.environ.copy()
        )

        # Siempre marcamos como expired para no reintentar infinitamente
        update_session_status(session_id, "expired")

        if returncode == 0:
            cleaned_count += 1
            logger.info(f"[CLEANUP] Sesión {session_id} ({project_name}) detenida correctamente.")
        else:
            logger.error(f"[CLEANUP] Error al detener {project_name}: {stderr[-300:]}")

    return cleaned_count


async def start_cleanup_scheduler(interval_seconds: int = 300):
    """Tarea en segundo plano que limpia sesiones expiradas periódicamente."""
    logger.info(f"[CLEANUP] Scheduler iniciado (cada {interval_seconds} segundos).")
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            cleaned = await cleanup_expired_sessions()
            if cleaned > 0:
                logger.info(f"[CLEANUP] Ciclo finalizado: {cleaned} sesión(es) liberada(s).")
        except asyncio.CancelledError:
            logger.info("[CLEANUP] Scheduler detenido.")
            break
        except Exception as e:
            logger.exception(f"[CLEANUP] Error inesperado: {e}")