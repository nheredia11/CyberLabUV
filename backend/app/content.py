from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .config import get_settings
from .schemas import CatalogItem, ModuleDetail


class ContentError(RuntimeError):
    """Error controlado al leer contenido pedagógico del simulador."""


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise ContentError(f"No existe el archivo requerido: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ContentError(f"No existe el archivo requerido: {path}")
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ContentError(f"El archivo YAML no tiene estructura de objeto: {path}")
    return data


def _read_text(path: Path) -> str:
    if not path.exists():
        raise ContentError(f"No existe el archivo requerido: {path}")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_catalog() -> list[CatalogItem]:
    settings = get_settings()
    data = _read_json(settings.scenario_catalog_path)
    return [CatalogItem(**item) for item in data]


def get_catalog_item(module_id: str) -> CatalogItem | None:
    normalized = module_id.upper()
    return next((item for item in load_catalog() if item.id.upper() == normalized), None)


@lru_cache(maxsize=32)
def load_module(module_id: str) -> ModuleDetail:
    catalog_item = get_catalog_item(module_id)
    if catalog_item is None:
        raise ContentError(f"No existe el módulo en el catálogo: {module_id}")

    settings = get_settings()
    module_path = settings.root_dir / catalog_item.ruta
    metadata = _read_yaml(module_path / "module.yaml")
    theory_markdown = _read_text(module_path / "theory.md")
    checkpoints = _read_json(module_path / "checkpoints.json")
    survey = _read_json(module_path / "survey.json")

    return ModuleDetail(
        **metadata,
        theory_markdown=theory_markdown,
        checkpoints=checkpoints,
        survey=survey,
        catalog=catalog_item,
    )


def load_all_modules() -> list[ModuleDetail]:
    modules = [load_module(item.id) for item in load_catalog()]
    return sorted(modules, key=lambda module: module.orden)


def clear_content_cache() -> None:
    load_catalog.cache_clear()
    load_module.cache_clear()