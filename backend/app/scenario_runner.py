from __future__ import annotations
import asyncio
import os
import socket
import uuid
import logging
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
from datetime import datetime, timedelta, timezone

from .config import get_settings
from .database import create_practice_session, get_active_session, update_session_status

logger = logging.getLogger("cyberlab")
settings = get_settings()

@dataclass(frozen=True)
class ScenarioDefinition:
    module_id: str
    slug: str
    compose_file: str
    description: str
    default_port: int
    env_port_var: str
    attacker_service: str

SCENARIOS: Dict[str, ScenarioDefinition] = {
    "S01": ScenarioDefinition("S01", "recon", "scenarios/recon/docker-compose.yml", "Reconocimiento de red", 8083, "RECON_PORT", "recon-attacker"),
    "S02": ScenarioDefinition("S02", "auth_http", "scenarios/auth_http/docker-compose.yml", "Autenticación HTTP", 8081, "AUTH_HTTP_PORT", "auth-attacker"),
    "S03": ScenarioDefinition("S03", "web_owasp", "scenarios/web_owasp/docker-compose.yml", "Prácticas OWASP", 8084, "OWASP_PORT", "web_owasp-attacker"),
    "S04": ScenarioDefinition("S04", "auth_services", "scenarios/auth_services/docker-compose.yml", "Autenticación SSH/FTP", 8085, "AUTH_SERVICES_PORT", "auth_services-attacker"),
    "S05": ScenarioDefinition("S05", "mitm_lab", "scenarios/mitm_lab/docker-compose.yml", "MITM en tráfico no cifrado", 8086, "MITM_PORT", "mitm-attacker"),
}

def find_free_port(start_port: int = 8100, max_tries: int = 200) -> int:
    for port in range(start_port, start_port + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError("No hay puertos disponibles en el host")

async def _run_cmd_async(
    cmd: list[str],
    cwd: Path,
    env: Optional[dict] = None,
    timeout: int = 180,
) -> Tuple[int, str, str]:
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

async def start_scenario_session(user_id: str, scenario_id: str, duration_minutes: int = 60) -> Tuple[bool, str, Dict]:
    normalized_id = scenario_id.upper()
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, f"Escenario {scenario_id} no encontrado", {}

    active = get_active_session(user_id, scenario.slug)
    if active:
        web_port = active["assigned_ports"]["web"]
        return True, "Sesión activa recuperada.", {
            "session_id": active["id"],
            "local_url": f"http://127.0.0.1:{web_port}",
            "status": active["status"]
        }

    session_id = str(uuid.uuid4())[:8]
    project_name = f"session_{session_id}"
    allocated_port = find_free_port()

    env = os.environ.copy()
    env[scenario.env_port_var] = str(allocated_port)

    compose_path = settings.root_dir / scenario.compose_file
    cmd = [
        "docker", "compose", 
        "-p", project_name, 
        "-f", str(compose_path), 
        "up", "-d", "--build"
    ]

    returncode, stdout, stderr = await _run_cmd_async(cmd, cwd=settings.root_dir, env=env)

    if returncode != 0:
        return False, f"Error al desplegar escenario: {stderr[-500:]}", {}

    try:
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat()
        assigned_ports = {"web": allocated_port}
        create_practice_session(
            session_id=session_id,
            user_id=user_id,
            scenario_slug=scenario.slug,
            docker_project_name=project_name,
            assigned_ports=assigned_ports,
            expires_at=expires_at
        )
    except Exception as e:
        logger.exception("Fallo al guardar la sesión en SQLite, realizando rollback de Docker")
        cleanup_cmd = ["docker", "compose", "-p", project_name, "-f", str(compose_path), "down", "-v", "--remove-orphans"]
        await _run_cmd_async(cleanup_cmd, cwd=settings.root_dir, env=env)
        return False, "Error interno al registrar la sesión de práctica.", {}

    return True, "Escenario desplegado exitosamente", {
        "session_id": session_id,
        "local_url": f"http://127.0.0.1:{allocated_port}",
        "status": "running"
    }

async def stop_scenario_session(user_id: str, scenario_id: str) -> Tuple[bool, str]:
    normalized_id = scenario_id.upper()
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, "Escenario no válido"

    active = get_active_session(user_id, scenario.slug)
    if not active:
        return True, "No había sesión activa para detener"

    project_name = active["docker_project_name"]
    compose_path = settings.root_dir / scenario.compose_file
    
    cmd = ["docker", "compose", "-p", project_name, "-f", str(compose_path), "down", "-v", "--remove-orphans"]
    returncode, _, stderr = await _run_cmd_async(cmd, cwd=settings.root_dir, env=os.environ.copy())

    if returncode == 0:
        update_session_status(active["id"], "stopped")
        return True, "Sesión y contenedores detenidos correctamente"
    
    return False, f"Falló al detener el contenedor: {stderr[-300:]}"

ALLOWED_COMMANDS = {
    "nmap", "ping", "curl", "cat", "ls", "whoami", "id",
    "nc", "dig", "grep", "echo", "pwd", "netstat", "ps", "head", "tail"
}
FORBIDDEN_CHARS = {";", "|", "&", "$", "`", ">", "<"}

async def run_scenario_command(user_id: str, scenario_id: str, command: str) -> Tuple[bool, str]:
    # 1. Validaciones de sintaxis y seguridad PRIMERO (para que los tests detecten comandos no permitidos correctamente)
    if len(command) > 300:
        return False, "Comando demasiado largo (máximo 300 caracteres)."

    if any(char in command for char in FORBIDDEN_CHARS):
        return False, "Comando rechazado: contiene caracteres prohibidos por motivos de seguridad."

    normalized_id = scenario_id.upper()
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, f"Escenario {scenario_id} no encontrado"

    try:
        parts = shlex.split(command)
    except ValueError:
        return False, "Error de sintaxis en el comando."

    if not parts:
        return False, "Comando vacío."

    base_cmd = parts[0].lower()
    if base_cmd not in ALLOWED_COMMANDS:
        return False, f"Comando '{base_cmd}' no permitido por la política de seguridad del simulador."

    # 2. Verificar el interruptor de entorno para ejecución real / simulada
    if not settings.allow_scenario_commands:
        return True, "Comando simulado (ALLOW_SCENARIO_COMMANDS=false)."

    # 3. Validar sesión activa en Docker
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

    returncode, stdout, stderr = await _run_cmd_async(cmd, cwd=settings.root_dir)
    if returncode != 0:
        return False, f"Error ejecutando comando: {stderr or stdout}"
    return True, stdout