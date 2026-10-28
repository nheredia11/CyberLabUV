from __future__ import annotations

import asyncio
import os
import shlex
import socket
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from .config import get_settings
from .database import (
    create_practice_session,
    get_active_session,
    update_session_status,
    connect,
    utcnow,
)


@dataclass(frozen=True)
class ScenarioDefinition:
    module_id: str
    slug: str
    compose_file: str
    description: str
    default_port: int
    env_port_var: str         # Variable de entorno que usa el docker-compose
    attacker_service: str     # Nombre del servicio atacante


SCENARIOS: Dict[str, ScenarioDefinition] = {
    "S01": ScenarioDefinition(
        module_id="S01",
        slug="recon",
        compose_file="scenarios/recon/docker-compose.yml",
        description="Reconocimiento de red y servicios",
        default_port=8083,
        env_port_var="RECON_PORT",
        attacker_service="recon-attacker",
    ),
    "S02": ScenarioDefinition(
        module_id="S02",
        slug="auth_http",
        compose_file="scenarios/auth_http/docker-compose.yml",
        description="Autenticación HTTP débil",
        default_port=8081,
        env_port_var="AUTH_HTTP_PORT",
        attacker_service="auth-attacker",
    ),
    "S03": ScenarioDefinition(
        module_id="S03",
        slug="web_owasp",
        compose_file="scenarios/web_owasp/docker-compose.yml",
        description="Aplicación web vulnerable OWASP",
        default_port=8084,
        env_port_var="OWASP_PORT",
        attacker_service="web_owasp-attacker",  # Corregido a web_owasp-attacker
    ),
    "S04": ScenarioDefinition(
        module_id="S04",
        slug="auth_services",
        compose_file="scenarios/auth_services/docker-compose.yml",
        description="Autenticación SSH y FTP",
        default_port=8085,
        env_port_var="AUTH_SERVICES_PORT",
        attacker_service="auth_services-attacker",
    ),
    "S05": ScenarioDefinition(
        module_id="S05",
        slug="mitm_lab",
        compose_file="scenarios/mitm_lab/docker-compose.yml",
        description="MITM en tráfico no cifrado",
        default_port=8086,
        env_port_var="MITM_PORT",
        attacker_service="mitm-attacker",
    ),
}


def find_free_port(start_port: int = 8100, max_tries: int = 300) -> int:
    """Busca un puerto libre en el host."""
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No se encontró un puerto libre en el rango configurado")


async def _run_cmd_async(
    cmd: list[str],
    cwd: Path,
    env: Optional[dict] = None,
    timeout: int = 180,
) -> Tuple[int, str, str]:
    """Ejecuta un comando de forma asíncrona."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env or os.environ.copy(),
    )

    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        return (
            process.returncode or 0,
            stdout.decode("utf-8", errors="replace"),
            stderr.decode("utf-8", errors="replace"),
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return -1, "", f"Timeout después de {timeout} segundos"


async def start_scenario_session(
    user_id: str,
    scenario_id: str,
    duration_minutes: int = 90,
) -> Tuple[bool, str, dict]:
    """
    Inicia un escenario de forma aislada para un estudiante.
    Retorna: (success, message, data)
    """
    settings = get_settings()

    if not settings.allow_scenario_commands:
        return (
            False,
            "La ejecución de escenarios está desactivada. Activa ALLOW_SCENARIO_COMMANDS=true",
            {},
        )

    normalized_id = scenario_id.upper()
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, f"Escenario {scenario_id} no encontrado", {}

    # Reutilizar sesión activa si existe
    active = get_active_session(user_id, scenario.slug)
    if active:
        port = active["assigned_ports"].get("web", scenario.default_port)
        return True, "Sesión activa recuperada", {
            "session_id": active["id"],
            "local_url": f"http://127.0.0.1:{port}",
            "status": active["status"],
            "docker_project_name": active["docker_project_name"],
        }

    # Crear nueva sesión
    session_id = str(uuid.uuid4())
    project_name = f"session_{session_id}"
    allocated_port = find_free_port()

    compose_path = settings.root_dir / scenario.compose_file
    if not compose_path.exists():
        return False, f"No existe el archivo: {compose_path}", {}

    # Variables de entorno para el puerto dinámico
    env = os.environ.copy()
    env[scenario.env_port_var] = str(allocated_port)

    cmd = [
        "docker", "compose",
        "-p", project_name,
        "-f", str(compose_path),
        "up", "-d", "--build",
    ]

    returncode, stdout, stderr = await _run_cmd_async(
        cmd, cwd=settings.root_dir, env=env
    )

    status_event = "ok" if returncode == 0 else "error"
    message_event = "Escenario desplegado correctamente" if returncode == 0 else f"Error al desplegar: {stderr[-600:]}"

    with connect() as conn:
        conn.execute(
            "INSERT INTO scenario_events(user_id, scenario_id, action, status, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, normalized_id, "start", status_event, message_event, utcnow()),
        )

    if returncode != 0:
        return False, message_event, {}

    assigned_ports = {"web": allocated_port}
    create_practice_session(
        user_id=user_id,
        scenario_slug=scenario.slug,
        docker_project_name=project_name,
        assigned_ports=assigned_ports,
        duration_minutes=duration_minutes,
        session_id=session_id,
    )

    return True, "Escenario desplegado correctamente", {
        "session_id": session_id,
        "local_url": f"http://127.0.0.1:{allocated_port}",
        "status": "running",
        "docker_project_name": project_name,
        "assigned_ports": assigned_ports,
    }


async def stop_scenario_session(
    user_id: str,
    scenario_id: str,
) -> Tuple[bool, str]:
    """Detiene y limpia los contenedores de una sesión."""
    settings = get_settings()

    normalized_id = scenario_id.upper()
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, "Escenario no válido"

    active = get_active_session(user_id, scenario.slug)
    if not active:
        return True, "No había sesión activa para detener"

    project_name = active["docker_project_name"]
    compose_path = settings.root_dir / scenario.compose_file

    cmd = [
        "docker", "compose",
        "-p", project_name,
        "-f", str(compose_path),
        "down", "--remove-orphans", "-v",
    ]

    returncode, stdout, stderr = await _run_cmd_async(
        cmd, cwd=settings.root_dir
    )

    update_session_status(active["id"], "stopped")
    status_event = "ok" if returncode == 0 else "error"
    msg = "Sesión detenida correctamente" if returncode == 0 else f"Problemas al limpiar: {stderr[-400:]}"

    with connect() as conn:
        conn.execute(
            "INSERT INTO scenario_events(user_id, scenario_id, action, status, message, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, normalized_id, "stop", status_event, msg, utcnow()),
        )

    if returncode == 0:
        return True, "Sesión y contenedores detenidos correctamente"
    
    return False, f"Se marcó como detenida, pero hubo problemas al limpiar contenedores: {stderr[-400:]}"


async def run_scenario_action(scenario_id: str, action: str, user_id: str = "anonymous") -> Tuple[bool, int | None, str, str, str]:
    """Función de compatibilidad."""
    act = action.lower()
    if act == "start":
        success, message, _ = await start_scenario_session(user_id, scenario_id)
        return success, 0 if success else 1, "", "", message

    if act in ("stop", "down"):
        success, message = await stop_scenario_session(user_id, scenario_id)
        return success, 0 if success else 1, "", "", message

    return False, None, "", "", f"Acción no soportada: {action}"


# Lista blanca estricta de comandos permitidos en el entorno controlado
ALLOWED_COMMANDS = {
    "nmap", "ping", "curl", "cat", "ls", "whoami", "id", 
    "nc", "dig", "grep", "echo", "pwd", "netstat", "ps", "head", "tail"
}

FORBIDDEN_CHARS = {";", "|", "&", "$", "`", ">", "<"}


async def run_scenario_command(
    user_id: str,
    scenario_id: str,
    command: str,
) -> Tuple[bool, str]:
    """
    Ejecuta un comando permitido dentro del contenedor atacante de la sesión activa del estudiante.
    Valida longitud, lista blanca con shlex, y registra en terminal_commands.
    """
    settings = get_settings()
    normalized_id = scenario_id.upper()
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, f"Escenario {scenario_id} no encontrado"

    # Validar longitud máxima de comando
    if not command or len(command.strip()) > 300:
        return False, "Comando vacío o excede la longitud máxima permitida (300 caracteres)."

    if any(char in command for char in FORBIDDEN_CHARS):
        return False, "Comando rechazado: contiene caracteres prohibidos por motivos de seguridad."

    try:
        parts = shlex.split(command.strip())
    except ValueError as e:
        return False, f"Error al parsear el comando: {e}"

    if not parts:
        return False, "Comando vacío."

    base_cmd = parts[0].lower()
    if base_cmd not in ALLOWED_COMMANDS:
        status_val = "blocked"
        output_msg = f"Comando '{base_cmd}' no permitido por la política de seguridad del simulador."
        with connect() as conn:
            conn.execute(
                "INSERT INTO terminal_commands(user_id, scenario_id, command, status, output, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, normalized_id, command.strip(), status_val, output_msg, utcnow()),
            )
        return False, output_msg

    active = get_active_session(user_id, scenario.slug)
    if not active:
        return False, "No hay una sesión activa para este escenario. Inícialo primero."

    project_name = active["docker_project_name"]
    compose_path = settings.root_dir / scenario.compose_file
    service_name = scenario.attacker_service

    cmd = [
        "docker", "compose",
        "-p", project_name,
        "-f", str(compose_path),
        "exec", "-T", service_name,
    ] + parts

    returncode, stdout, stderr = await _run_cmd_async(cmd, cwd=settings.root_dir, timeout=30)

    if returncode != 0:
        output_msg = f"Error ejecutando comando: {stderr or stdout}"
        status_val = "error"
    else:
        output_msg = stdout
        status_val = "ok"

    with connect() as conn:
        conn.execute(
            "INSERT INTO terminal_commands(user_id, scenario_id, command, status, output, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, normalized_id, command.strip(), status_val, output_msg, utcnow()),
        )

    if returncode != 0:
        return False, output_msg

    return True, stdout