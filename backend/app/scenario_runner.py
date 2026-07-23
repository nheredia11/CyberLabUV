from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import get_settings
from .storage import save_scenario_event


@dataclass(frozen=True)
class ScenarioDefinition:
    module_id: str
    slug: str
    compose_file: str
    description: str
    local_url: str


SCENARIOS: dict[str, ScenarioDefinition] = {
    "S01": ScenarioDefinition(
        module_id="S01",
        slug="recon",
        compose_file="scenarios/recon/docker-compose.yml",
        description="Reconocimiento de red y servicios",
        local_url="http://127.0.0.1:8083",
    ),
    "S02": ScenarioDefinition(
        module_id="S02",
        slug="auth_http",
        compose_file="scenarios/auth_http/docker-compose.yml",
        description="Autenticación HTTP débil en entorno controlado",
        local_url="http://127.0.0.1:8081",
    ),
    "S03": ScenarioDefinition(
        module_id="S03",
        slug="web_owasp",
        compose_file="scenarios/web_owasp/docker-compose.yml",
        description="Aplicación web vulnerable para prácticas OWASP",
        local_url="http://127.0.0.1:8084",
    ),
    "S04": ScenarioDefinition(
        module_id="S04",
        slug="auth_services",
        compose_file="scenarios/auth_services/docker-compose.yml",
        description="Autenticación simulada sobre servicios SSH y FTP",
        local_url="http://127.0.0.1:8085",
    ),
    "S05": ScenarioDefinition(
        module_id="S05",
        slug="mitm_lab",
        compose_file="scenarios/mitm_lab/docker-compose.yml",
        description="MITM simulado en tráfico no cifrado",
        local_url="http://127.0.0.1:8086",
    ),
}


def _docker_is_available() -> bool:
    return shutil.which("docker") is not None


def _compose_command(compose_path: Path) -> list[str]:
    settings = get_settings()
    env_file = settings.root_dir / ".env"

    command = ["docker", "compose"]

    if env_file.exists():
        command.extend(["--env-file", str(env_file)])

    command.extend(["-f", str(compose_path)])
    return command


def _run_command(command: list[str], cwd: Path, timeout: int = 120) -> tuple[int | None, str, str]:
    try:
        process = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return process.returncode, process.stdout, process.stderr
    except FileNotFoundError as exc:
        return None, "", f"No se encontró el ejecutable requerido: {exc}"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return None, stdout, f"Tiempo de espera agotado. {stderr}".strip()


def run_scenario_action(scenario_id: str, action: str) -> tuple[bool, int | None, str, str, str]:
    settings = get_settings()

    normalized_id = scenario_id.upper()
    normalized_action = action.lower().strip()

    if normalized_action not in {"start", "stop", "restart", "status", "logs"}:
        return False, None, "", "", f"Acción no permitida: {action}."

    if not settings.allow_scenario_commands:
        return (
            False,
            None,
            "",
            "",
            "La ejecución de escenarios está desactivada. Activa ALLOW_SCENARIO_COMMANDS=true en .env y reinicia el backend.",
        )

    if not _docker_is_available():
        return (
            False,
            None,
            "",
            "",
            "Docker no está disponible. Verifica que Docker Desktop esté instalado y abierto.",
        )

    scenario = SCENARIOS.get(normalized_id)
    if scenario is None:
        return False, None, "", "", f"No existe configuración de escenario para {scenario_id}."

    compose_path = settings.root_dir / scenario.compose_file

    if not compose_path.exists():
        return False, None, "", "", f"No existe el docker-compose.yml del escenario: {compose_path}"

    base_command = _compose_command(compose_path)

    if normalized_action == "start":
        command = base_command + ["up", "-d", "--build"]
    elif normalized_action == "stop":
        command = base_command + ["down", "--remove-orphans"]
    elif normalized_action == "status":
        command = base_command + ["ps"]
    elif normalized_action == "logs":
        command = base_command + ["logs", "--tail", "120"]
    else:
        stop_code, stop_out, stop_err = _run_command(
            base_command + ["down", "--remove-orphans"],
            cwd=settings.root_dir,
        )
        start_code, start_out, start_err = _run_command(
            base_command + ["up", "-d", "--build"],
            cwd=settings.root_dir,
        )

        stdout = f"{stop_out}\n{start_out}".strip()
        stderr = f"{stop_err}\n{start_err}".strip()
        returncode = start_code if start_code is not None else stop_code

        save_scenario_event(normalized_id, normalized_action, returncode, stdout, stderr)

        if returncode == 0:
            return True, returncode, stdout, stderr, f"Escenario {normalized_id} reiniciado correctamente. URL: {scenario.local_url}"

        return True, returncode, stdout, stderr, f"El reinicio de {normalized_id} terminó con errores."

    returncode, stdout, stderr = _run_command(command, cwd=settings.root_dir)
    save_scenario_event(normalized_id, normalized_action, returncode, stdout, stderr)

    if returncode == 0:
        return True, returncode, stdout, stderr, f"Acción {normalized_action} ejecutada correctamente para {normalized_id}. URL: {scenario.local_url}"

    return True, returncode, stdout, stderr, f"La acción {normalized_action} terminó con código {returncode}."


# --- AÑADIR AL FINAL DE scenario_runner.py ---

# LISTA BLANCA DE COMANDOS (Hardening - Previene Command Injection)
SAFE_COMMANDS = {
    "S01": [
        "nmap -sV recon-lab",
        "curl http://recon-lab:5000/health"
    ],
    "S02": [
        "hydra -l estudiante -P wordlists/demo.txt localhost http-post-form",
        "curl -i http://127.0.0.1:8081/health"
    ]
}

def run_terminal_command(scenario_id: str, command: str) -> tuple[bool, int | None, str, str, str]:
    settings = get_settings()
    normalized_id = scenario_id.upper()
    clean_command = command.strip()

    # 1. Validación estricta de seguridad
    if normalized_id not in SAFE_COMMANDS or clean_command not in SAFE_COMMANDS.get(normalized_id, []):
        return False, None, "", "", f"Error de seguridad: El comando '{clean_command}' no está permitido en este escenario."

    # 2. Obtener configuración del escenario
    scenario = SCENARIOS.get(normalized_id)
    if not scenario:
        return False, None, "", "", "Escenario no configurado."

    compose_path = settings.root_dir / scenario.compose_file
    base_command = _compose_command(compose_path)
    
    # 3. Construir el comando para ejecutar DENTRO del contenedor atacante
    # Asumimos que la máquina atacante siempre se llama {slug}-attacker (ej: recon-attacker)
    attacker_service = f"{scenario.slug}-attacker"
    
    # docker compose -f <file> exec -T <servicio> sh -c "<comando>"
    exec_cmd = base_command + ["exec", "-T", attacker_service, "sh", "-c", clean_command]

    # 4. Ejecutar y retornar resultados
    returncode, stdout, stderr = _run_command(exec_cmd, cwd=settings.root_dir)

    if returncode == 0:
        return True, returncode, stdout, stderr, "Comando ejecutado correctamente."
    return True, returncode, stdout, stderr, f"El comando falló con código {returncode}."