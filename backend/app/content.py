from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml
from .schemas import CatalogItem, ModuleDetail, CheckpointDef

MODULES_DIR = Path(__file__).resolve().parent.parent.parent / "platform" / "modules"


def _load_module_from_disk(module_path: Path) -> ModuleDetail | None:
    try:
        yaml_path = module_path / "module.yaml"
        theory_path = module_path / "theory.md"
        checkpoints_path = module_path / "checkpoints.json"
        survey_path = module_path / "survey.json"

        meta = {}
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}

        theory = ""
        if theory_path.exists():
            theory = theory_path.read_text(encoding="utf-8")

        checkpoints_data = []
        if checkpoints_path.exists():
            with open(checkpoints_path, "r", encoding="utf-8") as f:
                checkpoints_data = json.load(f) or []

        survey_data = []
        if survey_path.exists():
            with open(survey_path, "r", encoding="utf-8") as f:
                survey_data = json.load(f) or []

        mod_id = meta.get("id", module_path.name.upper())
        title = meta.get("titulo", meta.get("title", mod_id))
        description = meta.get("descripcion", meta.get("description", ""))
        category = meta.get("category", "general")
        difficulty = meta.get("difficulty", "beginner")
        estimated_hours = meta.get("estimated_hours", 2)
        route = meta.get("route", meta.get("ruta", f"/modules/{mod_id.lower()}"))
        active = meta.get("active", True)
        orden = meta.get("orden", meta.get("order", 0))

        checkpoints_objs = [CheckpointDef(**cp) for cp in checkpoints_data]

        return ModuleDetail(
            id=mod_id,
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            estimated_hours=estimated_hours,
            route=route,
            active=active,
            orden=orden,
            theory=theory,
            checkpoints=checkpoints_objs,
            survey=survey_data,
        )
    except Exception as e:
        print(f"Error cargando módulo {module_path.name}: {e}")
        return None


def load_catalog() -> list[CatalogItem]:
    items = []
    if MODULES_DIR.exists():
        for subfolder in sorted(MODULES_DIR.iterdir()):
            if subfolder.is_dir():
                detail = _load_module_from_disk(subfolder)
                if detail and detail.active:
                    items.append(
                        CatalogItem(
                            id=detail.id,
                            title=detail.title,
                            description=detail.description,
                            category=detail.category,
                            difficulty=detail.difficulty,
                            estimated_hours=detail.estimated_hours,
                            route=detail.route,
                            active=detail.active,
                            orden=detail.orden,
                        )
                    )
    return sorted(items, key=lambda x: x.orden)


def load_module(module_id: str) -> ModuleDetail | None:
    if not MODULES_DIR.exists():
        return None
    for subfolder in MODULES_DIR.iterdir():
        if subfolder.is_dir():
            if subfolder.name.upper() == module_id.upper() or subfolder.name.lower().replace("_", "") == module_id.lower().replace("_", ""):
                return _load_module_from_disk(subfolder)
            meta_file = subfolder / "module.yaml"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = yaml.safe_load(f) or {}
                        if meta.get("id", "").upper() == module_id.upper():
                            return _load_module_from_disk(subfolder)
                except Exception:
                    pass
    return None


def load_all_modules() -> list[ModuleDetail]:
    modules = []
    if MODULES_DIR.exists():
        for subfolder in MODULES_DIR.iterdir():
            if subfolder.is_dir():
                mod = _load_module_from_disk(subfolder)
                if mod:
                    modules.append(mod)
    return sorted(modules, key=lambda m: getattr(m, "orden", 0))