from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .config import get_settings

MODULE_DIRS = {
    "M00": "M00_induccion",
    "S01": "S01_reconocimiento",
    "S02": "S02_autenticacion_http",
    "S03": "S03_web_basico",
}

@lru_cache(maxsize=1)
def load_catalog() -> list[dict[str, Any]]:
    path = get_settings().catalog_path
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def module_path(module_id: str) -> Path:
    dirname = MODULE_DIRS.get(module_id, module_id)
    return get_settings().modules_dir / dirname

def _read_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

def _read_yaml(path: Path, default: Any) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else default

def _read_text(path: Path, default: str = "") -> str:
    return path.read_text(encoding="utf-8") if path.exists() else default

@lru_cache(maxsize=32)
def load_module(module_id: str) -> dict[str, Any]:
    base = module_path(module_id)
    meta = _read_yaml(base / "module.yaml", {})
    catalog_item = next((item for item in load_catalog() if item.get("id") == module_id), {})
    return {
        **catalog_item,
        **meta,
        "id": meta.get("id", module_id),
        "module_id": module_id,
        "theory": _read_text(base / "theory.md"),
        "checkpoints": _read_json(base / "checkpoints.json", []),
        "survey": _read_json(base / "survey.json", []),
    }

def load_modules() -> list[dict[str, Any]]:
    modules = [load_module(item["id"]) for item in load_catalog()]
    return sorted(modules, key=lambda m: int(m.get("orden", 999)))

def scenario_slug_for_module(module_id: str) -> str | None:
    mapping = {"S01": "recon", "S02": "auth_http", "S03": "webapp"}
    return mapping.get(module_id)
