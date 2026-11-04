"""Rutas: checkpoints."""
from __future__ import annotations

import logging
from fastapi import HTTPException, Depends


from ..schemas import (
    CheckpointSubmission,
)
from ..storage import (
    save_checkpoint,
)
from ..auth import (
    get_current_user,
)
from ..config import get_settings

from fastapi import APIRouter

logger = logging.getLogger("cyberlab")
settings = get_settings()
router = APIRouter()


@router.post("/api/checkpoints/submit")
async def submit_checkpoint(submission: CheckpointSubmission, current_user: dict = Depends(get_current_user)):
    token_user_id = current_user.get("user_id")
    if current_user.get("role") != "teacher":
        submission.student_id = token_user_id

    try:
        result = save_checkpoint(submission)
    except ValueError as e:
        raise HTTPException(status_code=422, detail="Datos de checkpoint inválidos o no cumplen con la validación.")
    except Exception as e:
        logger.exception("Error interno al registrar checkpoint: %s", e)
        raise HTTPException(status_code=500, detail="Error interno al procesar el checkpoint.")

    return {"status": "ok", "result": result}
