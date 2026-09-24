from __future__ import annotations

from typing import Any
from .schemas import CatalogItem, ModuleDetail, CheckpointDef

MOCK_CATALOG = [
    {
        "id": "S01",
        "title": "Introducción a la Ciberseguridad",
        "description": "Fundamentos de la seguridad",
        "category": "general",
        "difficulty": "beginner",
        "estimated_hours": 2,
        "route": "/modules/s01",
        "active": True,
    },
    {
        "id": "S02",
        "title": "Criptografía Básica",
        "description": "Cifrado simétrico y asimétrico",
        "category": "crypto",
        "difficulty": "intermediate",
        "estimated_hours": 3,
        "route": "/modules/s02",
        "active": True,
    },
]


def load_catalog() -> list[CatalogItem]:
  items = []
  for raw_item in MOCK_CATALOG:
    item = CatalogItem(**raw_item)
    _ = item.route  # Corregido: usa catalog_item.route
    items.append(item)
  return items


def load_all_modules():
    # Cargar módulos del catálogo
    raw_modules = [load_module(item.id) for item in load_catalog()]
    
    # 1. Filtrar los módulos que hayan devuelto None
    modules = [m for m in raw_modules if m is not None]
    
    # 2. Ordenar de forma segura manejando la falta del atributo 'orden' o valores None
    return sorted(
        modules, 
        key=lambda module: getattr(module, "orden", 0) if getattr(module, "orden", None) is not None else 0
    )