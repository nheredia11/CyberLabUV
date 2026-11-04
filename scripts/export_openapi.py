"""Genera backend/openapi.snapshot.json a partir de la app FastAPI.

Uso:  PYTHONPATH=backend python scripts/export_openapi.py
Ejecutar al cambiar rutas o modelos de respuesta y versionar el resultado.
"""
import json
import pathlib

from app.main import app

out = pathlib.Path(__file__).resolve().parent.parent / "backend" / "openapi.snapshot.json"
out.write_text(json.dumps(app.openapi(), indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
print(f"Snapshot escrito en {out}")
