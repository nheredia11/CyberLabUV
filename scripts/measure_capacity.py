"""Medición de capacidad del servidor según el número de usuarios concurrentes.

Levanta N sesiones reales (una por estudiante simulado, rotando S01..S05), mide memoria, CPU y
disco de los contenedores en reposo, y luego ejecuta un comando por sesión a la vez (pico de carga).
Con eso estima los recursos por usuario para dimensionar el servidor (manual del administrador).

Uso (desde la raíz del repo, con Docker en marcha):
    python scripts/measure_capacity.py --max 10 --out docs/capacidad.json

Advertencia: crea hasta --max sesiones reales; ciérralas con Ctrl+C si hace falta (se limpian al final).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
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
SCENARIOS = ["S01", "S02", "S03", "S04", "S05"]
LOAD = {
    "S01": "nmap -sT -p 1-2000 recon-lab",
    "S02": 'hydra -l estudiante -P /usr/share/wordlists/demo.txt -s 5000 auth-lab http-post-form "/auth-http/login:username=^USER^&password=^PASS^:F=auth=fail"',
    "S03": "curl -s 'http://web-owasp-lab:5000/web/search?q=1%20OR%201=1'",
    "S04": "nmap -sT -p 1-2000 auth-services-lab",
    "S05": "curl -s http://mitm-lab:5000/events",
}
UNITS = {"GiB": 1024, "MiB": 1, "KiB": 1 / 1024, "GB": 1000, "MB": 1, "kB": 1 / 1000, "B": 1 / 1_000_000}


def _to_mib(text: str) -> float:
    text = text.strip()
    for unit, factor in UNITS.items():
        if text.endswith(unit):
            return float(text[: -len(unit)]) * factor
    return 0.0


def docker_stats() -> tuple[int, float, float]:
    out = subprocess.run(["docker", "stats", "--no-stream", "--format", "{{json .}}"], capture_output=True, text=True).stdout
    rows = [json.loads(line) for line in out.splitlines() if "session_" in line]
    mem = sum(_to_mib(r["MemUsage"].split("/")[0]) for r in rows)
    cpu = sum(float(r["CPUPerc"].rstrip("%")) for r in rows)
    return len(rows), mem, cpu


def docker_disk() -> float:
    out = subprocess.run(["docker", "ps", "-s", "--filter", "name=session_", "--format", "{{.Size}}"], capture_output=True, text=True).stdout
    return sum(_to_mib(line.split("(")[0]) for line in out.splitlines())


async def main(nmax: int, out: Path | None) -> None:
    runner.settings.max_sessions_total = max(nmax, runner.settings.max_sessions_total)
    rows, started = [], []
    try:
        for n in range(1, nmax + 1):
            sid = SCENARIOS[(n - 1) % len(SCENARIOS)]
            t0 = time.time()
            ok, msg, _ = await runner.start_scenario_session(f"cap_{n}", sid)
            if not ok:
                print(f"La sesión {n} no inició: {msg[-200:]}")
                break
            started.append((f"cap_{n}", sid))
            await asyncio.sleep(4)
            containers, mem, cpu = docker_stats()
            row = {"sesiones": n, "contenedores": containers, "memoria_mib": round(mem, 1),
                   "cpu_pct": round(cpu, 1), "disco_mib": round(docker_disk(), 2), "arranque_s": round(time.time() - t0 - 4, 1)}
            rows.append(row)
            print(row, flush=True)

        async def peak():
            samples = []
            for _ in range(8):
                samples.append(await asyncio.to_thread(docker_stats))
                await asyncio.sleep(0.5)
            return max(s[2] for s in samples), max(s[1] for s in samples)

        t0 = time.time()
        (cpu_peak, mem_peak), results = await asyncio.gather(
            peak(), asyncio.gather(*(runner.run_scenario_command(u, s, LOAD[s]) for u, s in started))
        )
        load = {"sesiones_con_carga": len(started), "cpu_pct_pico": round(cpu_peak, 1), "memoria_mib_pico": round(mem_peak, 1),
                "duracion_s": round(time.time() - t0, 1), "comandos_ok": sum(1 for ok, _ in results if ok)}
        print(load, flush=True)
    finally:
        for user, sid in started:
            await runner.stop_scenario_session(user, sid)

    if rows:
        per_user_mem = round(rows[-1]["memoria_mib"] / rows[-1]["sesiones"], 1)
        per_user_disk = round(rows[-1]["disco_mib"] / rows[-1]["sesiones"], 2)
        cpu_per_user_peak = round(load["cpu_pct_pico"] / max(load["sesiones_con_carga"], 1), 1)
        summary = {
            "host_cpus": os.cpu_count(),
            "memoria_por_sesion_mib": per_user_mem,
            "disco_por_sesion_mib": per_user_disk,
            "cpu_pico_por_sesion_pct": cpu_per_user_peak,
            "sesiones_por_nucleo_en_pico": round(100 / cpu_per_user_peak, 1) if cpu_per_user_peak else None,
        }
        print("\nResumen:", summary)
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"filas": rows, "carga": load, "resumen": summary}, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"Guardado en {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--max", type=int, default=10, help="número máximo de sesiones simultáneas")
    parser.add_argument("--out", type=Path, default=None, help="archivo JSON de resultados")
    args = parser.parse_args()
    asyncio.run(main(args.max, args.out))
