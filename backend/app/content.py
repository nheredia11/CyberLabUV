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


def load_module(module_id: str) -> ModuleDetail | None:
  catalog = load_catalog()
  found = next((item for item in catalog if item.id == module_id), None)
  if not found:
    return None

  return ModuleDetail(
      id=found.id,
      title=found.title,
      description=found.description,
      category=found.category,
      difficulty=found.difficulty,
      estimated_hours=found.estimated_hours,
      route=found.route,
      active=found.active,
      checkpoints=[
          CheckpointDef(
              id=f"{found.id}_cp1",
              title="Checkpoint 1",
              type="flag",
              question="¿Cuál es la bandera?",
              points=10,
          )
      ],
  )