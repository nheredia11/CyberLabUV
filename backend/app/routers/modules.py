"""Rutas: modules."""
from __future__ import annotations

import logging
from fastapi import HTTPException, Depends


from ..schemas import (
    CatalogItem,
    ModuleDetail,
)
from ..content import load_catalog, load_module
from ..storage import (
    get_student_module_progress,
)
from ..auth import (
    get_current_user,
    get_optional_user,
)
from ..dashboard import get_student_progress_state
from ..config import get_settings

from fastapi import APIRouter

logger = logging.getLogger("cyberlab")
settings = get_settings()
router = APIRouter()


@router.get("/api/modules", response_model=list[CatalogItem])
@router.get("/api/catalog", response_model=list[CatalogItem])
async def list_modules():
    return load_catalog()


@router.get("/api/modules/{module_id}", response_model=ModuleDetail)
@router.get("/api/catalog/{module_id}", response_model=ModuleDetail)
async def get_module(module_id: str, current_user: dict | None = Depends(get_optional_user)):
    detail = load_module(module_id)
    if not detail:
        raise HTTPException(
            status_code=404, detail=f"Módulo {module_id} no encontrado"
        )
    # El progreso se toma del token, nunca del user_id de la URL (evita ver datos de otro estudiante).
    if current_user:
        done, surveys = get_student_progress_state(current_user["user_id"])
        done_ids = done.get(detail.id, set())
        for checkpoint in detail.checkpoints:
            checkpoint.completed = checkpoint.id in done_ids
        detail.survey_completed = detail.id in surveys
    return detail


@router.get("/api/modules/{module_id}/feedback")
async def get_module_feedback(module_id: str, user_id: str, current_user: dict = Depends(get_current_user)) -> dict[str, str]:
    if current_user.get("role") != "teacher" and current_user.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    progress = get_student_module_progress(user_id, module_id)
    if not progress or progress.get("progress_percent", 0) == 0:
        return {
            "level": "Inicial", 
            "message": "Inicia la práctica y guarda tus primeros checkpoints para recibir orientación."
        }
    if progress.get("progress_percent", 0) >= 100:
        return {
            "level": "Autónomo", 
            "message": "¡Excelente! Has dominado el escenario por completo y validado todos tus hallazgos."
        }
    return {
        "level": "En consolidación",
        "message": f"Vas por buen camino. Has completado {progress.get('checkpoints_completed', 0)} checkpoint(s). Continúa extrayendo evidencia."
    }
