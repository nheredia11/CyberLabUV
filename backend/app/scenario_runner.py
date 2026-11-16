from __future__ import annotations
import asyncio
import json
import os
import uuid
import logging
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta, timezone

from .config import get_settings
from .lab_access import edge_network, lab_path, own_container_id, running_in_container
from .database import count_running_sessions, create_practice_session, get_active_session, update_session_status

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
    lab_service: str

SCENARIOS: Dict[str, ScenarioDefinition] = {
    "S01": ScenarioDefinition("S01", "recon", "scenarios/recon/docker-compose.yml", "Reconocimiento de red", 8083, "RECON_PORT", "recon-attacker", "recon-lab"),
    "S02": ScenarioDefinition("S02", "auth_http", "scenarios/auth_http/docker-compose.yml", "Autenticación HTTP", 8081, "AUTH_HTTP_PORT", "auth-attacker", "auth-lab"),
    "S03": ScenarioDefinition("S03", "web_owasp", "scenarios/web_owasp/docker-compose.yml", "Prácticas OWASP", 8084, "OWASP_PORT", "web_owasp-attacker", "web_owasp-lab"),
    "S04": ScenarioDefinition("S04", "auth_services", "scenarios/auth_services/docker-compose.yml", "Autenticación SSH/FTP", 8085, "AUTH_SERVICES_PORT", "auth_services-attacker", "auth_services-lab"),
    "S05": ScenarioDefinition("S05", "mitm_lab", "scenarios/mitm_lab/docker-compose.yml", "MITM en tráfico no cifrado", 8086, "MITM_PORT", "mitm-attacker", "mitm-lab"),
}

def parse_published_port(output: str) -> int | None:
    """Extrae el puerto de la salida de `docker compose port` (p. ej. '127.0.0.1:49153')."""
    lines = output.strip().splitlines()
    match = re.search(r":(\d{2,5})\s*$", lines[0]) if lines else None
    return int(match.group(1)) if match else None


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

    if count_running_sessions(user_id) >= settings.max_sessions_per_user:
        return False, (
            f"Ya tienes {settings.max_sessions_per_user} escenarios activos. "
            "Detén uno antes de iniciar otro."
        ), {}
    if count_running_sessions() >= settings.max_sessions_total:
        return False, "El simulador está al límite de capacidad. Intenta de nuevo en unos minutos.", {}

    session_id = str(uuid.uuid4())[:8]
    project_name = f"session_{session_id}"
    env = os.environ.copy()
    compose_path = settings.root_dir / scenario.compose_file
    base = ["docker", "compose", "-p", project_name, "-f", str(compose_path)]

    async def rollback() -> None:
        await teardown_project(project_name, scenario)

    # El puerto del host lo elige Docker (ports: "127.0.0.1::5000"). El backend corre dentro de un
    # contenedor y no puede saber qué puertos usa el host, así que no intentamos adivinarlo.
    returncode, stdout, stderr = await _run_cmd_async(base + ["up", "-d", "--build"], cwd=settings.root_dir, env=env)
    if returncode != 0:
        await rollback()  # no dejar contenedores ni redes a medias
        return False, f"Error al desplegar escenario: {stderr[-500:]}", {}

    rc, port_out, port_err = await _run_cmd_async(
        base + ["port", scenario.lab_service, "5000"], cwd=settings.root_dir, env=env
    )
    allocated_port = parse_published_port(port_out) if rc == 0 else None
    if allocated_port is None:
        logger.error("No se pudo leer el puerto publicado de %s: %s %s", scenario.lab_service, port_out, port_err)
        await rollback()
        return False, "El escenario arrancó pero no se pudo obtener su puerto. Intenta de nuevo.", {}

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
    except Exception:
        logger.exception("Fallo al guardar la sesión en SQLite, realizando rollback de Docker")
        await rollback()
        return False, "Error interno al registrar la sesión de práctica.", {}

    await attach_backend(project_name, scenario)

    return True, "Escenario desplegado exitosamente", {
        "session_id": session_id,
        "local_url": f"http://127.0.0.1:{allocated_port}",
        "lab_path": lab_path(session_id),
        "status": "running"
    }

def _compose_base(project_name: str, scenario: "ScenarioDefinition") -> list[str]:
    return ["docker", "compose", "-p", project_name, "-f", str(settings.root_dir / scenario.compose_file)]


async def attach_backend(project_name: str, scenario: "ScenarioDefinition") -> None:
    """Si el backend corre en Docker, lo conecta a la red no interna del laboratorio
    para poder servir su página por el proxy /labs/<sesión>/."""
    if not running_in_container():
        return  # en el host, las IP de las redes bridge ya son alcanzables
    rc, _, err = await _run_cmd_async(
        ["docker", "network", "connect", edge_network(project_name, scenario.slug), own_container_id()],
        cwd=settings.root_dir,
    )
    if rc != 0 and "already exists" not in err:
        logger.warning("No se pudo conectar el backend a la red del laboratorio: %s", err[-300:])


async def teardown_project(project_name: str, scenario: "ScenarioDefinition") -> tuple[int, str]:
    """Apaga una sesión: desconecta el backend de su red (si no, la red no se puede borrar)
    y ejecuta `down -v --remove-orphans`. Lo usan la parada manual, el rollback y la limpieza."""
    _lab_targets.pop(project_name, None)
    if running_in_container():
        await _run_cmd_async(
            ["docker", "network", "disconnect", "-f", edge_network(project_name, scenario.slug), own_container_id()],
            cwd=settings.root_dir,
        )
    rc, _, err = await _run_cmd_async(
        _compose_base(project_name, scenario) + ["down", "-v", "--remove-orphans"], cwd=settings.root_dir, env=os.environ.copy()
    )
    return rc, err


_lab_targets: dict[str, str] = {}


async def resolve_lab_target(project_name: str, scenario: "ScenarioDefinition") -> str | None:
    """URL base (http://IP:5000) del laboratorio en su red no interna."""
    if project_name in _lab_targets:
        return _lab_targets[project_name]
    rc, cid, _ = await _run_cmd_async(
        _compose_base(project_name, scenario) + ["ps", "-q", scenario.lab_service], cwd=settings.root_dir
    )
    cid = cid.strip().splitlines()[0] if rc == 0 and cid.strip() else ""
    if not cid:
        return None
    rc, out, _ = await _run_cmd_async(
        ["docker", "inspect", "-f", "{{json .NetworkSettings.Networks}}", cid], cwd=settings.root_dir
    )
    try:
        networks = json.loads(out) if rc == 0 else {}
    except json.JSONDecodeError:
        networks = {}
    ip = (networks.get(edge_network(project_name, scenario.slug)) or {}).get("IPAddress")
    if not ip:
        return None
    _lab_targets[project_name] = f"http://{ip}:5000"
    return _lab_targets[project_name]


async def stop_scenario_session(user_id: str, scenario_id: str) -> Tuple[bool, str]:
    normalized_id = scenario_id.upper()
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, "Escenario no válido"

    active = get_active_session(user_id, scenario.slug)
    if not active:
        return True, "No había sesión activa para detener"

    project_name = active["docker_project_name"]
    returncode, stderr = await teardown_project(project_name, scenario)

    if returncode == 0:
        update_session_status(active["id"], "stopped")
        return True, "Sesión y contenedores detenidos correctamente"
    
    return False, f"Falló al detener el contenedor: {stderr[-300:]}"

# Comandos permitidos en todos los escenarios.
BASE_COMMANDS = {
    "nmap", "ping", "curl", "cat", "ls", "whoami", "id", "nc", "dig",
    "grep", "echo", "pwd", "netstat", "ps", "head", "tail",
}
# Herramientas adicionales por escenario (principio de mínimo privilegio).
EXTRA_COMMANDS: Dict[str, set] = {
    "S02": {"hydra"},
    "S04": {"hydra", "ssh"},
    "S05": {"tcpdump"},
}
# Compatibilidad con código/pruebas que importan ALLOWED_COMMANDS.
ALLOWED_COMMANDS = set(BASE_COMMANDS).union(*EXTRA_COMMANDS.values())
# Siempre prohibidos (sustitución de comandos y saltos de línea).
FORBIDDEN_ALWAYS = {"$", "`", "\n", "\r"}
# Prohibidos fuera de comillas. Dentro de comillas son datos (p. ej. el formulario de hydra
# "/login:user=^USER^&pass=^PASS^:F=fail"); el comando se ejecuta sin shell, así que no se interpretan.
FORBIDDEN_UNQUOTED = {";", "|", "&", ">", "<"}
# Compatibilidad con código que importaba FORBIDDEN_CHARS.
FORBIDDEN_CHARS = FORBIDDEN_ALWAYS | FORBIDDEN_UNQUOTED
_QUOTED = re.compile(r"\"[^\"]*\"|'[^']*'")
MAX_OUTPUT_CHARS = 20_000
COMMAND_TIMEOUT_SECONDS = 60


def has_forbidden_chars(command: str) -> bool:
    if any(c in command for c in FORBIDDEN_ALWAYS):
        return True
    unquoted = _QUOTED.sub("", command)
    return any(c in unquoted for c in FORBIDDEN_UNQUOTED)


def allowed_commands_for(scenario_id: str) -> set:
    return BASE_COMMANDS | EXTRA_COMMANDS.get(scenario_id.upper(), set())


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return text[:MAX_OUTPUT_CHARS] + "\n... [salida truncada]"


async def run_scenario_command(user_id: str, scenario_id: str, command: str) -> Tuple[bool, str]:
    # 1. Validaciones de sintaxis y seguridad PRIMERO (para que los tests detecten comandos no permitidos correctamente)
    if len(command) > 300:
        return False, "Comando demasiado largo (máximo 300 caracteres)."

    if has_forbidden_chars(command):
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
    if base_cmd not in allowed_commands_for(normalized_id):
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

    returncode, stdout, stderr = await _run_cmd_async(
        cmd, cwd=settings.root_dir, timeout=COMMAND_TIMEOUT_SECONDS
    )
    if returncode == -1:
        return False, stderr
    if "is not running" in stderr:
        return False, "El escenario se está iniciando o reiniciando. Espera unos segundos y vuelve a intentarlo."
    output = (stdout + ("\n" + stderr if stderr else "")).strip()
    # Herramientas como hydra o nmap devuelven código != 0 en resultados válidos
    # (sin credenciales encontradas, host caído). Se muestra la salida al estudiante.
    if returncode != 0:
        if not output:
            return False, f"El comando terminó con código {returncode} sin salida."
        output += f"\n[código de salida: {returncode}]"
    return True, _truncate(output)
