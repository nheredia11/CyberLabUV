"""Verificación de punta a punta con Docker real.

Inicia cada escenario con el MISMO código del backend, ejecuta todos los comandos sugeridos de la
interfaz (frontend/src/content/safeCommands.json), revisa el aislamiento de red y detiene la sesión.

Uso (desde la raíz del repo, con Docker en marcha):
    python scripts/e2e_docker.py            # los cinco escenarios
    python scripts/e2e_docker.py S01 S02    # solo algunos

Termina con código 1 si algún escenario o comando falla.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("DATABASE_PATH", tempfile.mktemp(suffix=".db"))
os.environ["CYBERLAB_DB"] = os.environ["DATABASE_PATH"]
sys.path.insert(0, str(ROOT / "backend"))

from app.database import init_db  # noqa: E402

init_db()
import app.scenario_runner as runner  # noqa: E402

runner.settings.allow_scenario_commands = True

# El atacante NO debe salir a internet: estos comandos deben fallar.
ISOLATION = ["curl -s -m 4 http://1.1.1.1", "ping -c 1 -W 2 8.8.8.8"]
# Salidas esperadas por comando sugerido (si aparece el texto, el comando cumplió su objetivo).
EXPECT = {
    "nc -w 2 recon-lab 2222": "SSH-2.0",
    "curl -sI http://recon-lab:5000": "200 OK",
    "hydra": "1 valid password found",
    "1%20OR%201=1": '"admin"',
    "..%2Fetc%2Fpasswd": '"blocked":true',
    "mitm/send": "",
    "/events": '"items"',
}


def expected_for(command: str) -> str | None:
    for key, value in EXPECT.items():
        if key in command:
            return value
    return None


async def check(user: str, sid: str) -> list[str]:
    errors: list[str] = []
    commands = json.loads((ROOT / "frontend/src/content/safeCommands.json").read_text(encoding="utf-8"))[sid]
    t0 = time.time()
    ok, msg, data = await runner.start_scenario_session(user, sid)
    print(f"\n== {sid}: inicio {'OK' if ok else 'FALLÓ'} en {time.time() - t0:.1f}s  {data.get('lab_path', '')}")
    if not ok:
        return [f"{sid}: no inició: {msg[-300:]}"]
    try:
        await asyncio.sleep(2)
        for command in commands:
            ok, out = await runner.run_scenario_command(user, sid, command)
            want = expected_for(command)
            passed = ok and (want is None or want in out)
            print(f"   [{'OK ' if passed else 'ERR'}] {command[:90]}")
            if not passed:
                errors.append(f"{sid}: '{command}' -> {out.strip()[:200]}")
        for command in ISOLATION:
            ok, out = await runner.run_scenario_command(user, sid, command)
            leaked = ok and "[código de salida" not in out
            print(f"   [{'ERR' if leaked else 'OK '}] aislamiento: {command}")
            if leaked:
                errors.append(f"{sid}: el atacante tiene salida a internet ({command})")
    finally:
        await runner.stop_scenario_session(user, sid)
    return errors


async def main(selected: list[str]) -> int:
    errors: list[str] = []
    for sid in selected:
        errors += await check("e2e_docker", sid)
    print("\n" + ("Todo correcto." if not errors else "Fallos:\n- " + "\n- ".join(errors)))
    return 1 if errors else 0


if __name__ == "__main__":
    chosen = [a.upper() for a in sys.argv[1:]] or list(runner.SCENARIOS)
    sys.exit(asyncio.run(main(chosen)))
