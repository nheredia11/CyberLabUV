"""Rutas: surveys."""
from __future__ import annotations

import logging
from fastapi import HTTPException, Depends


from ..schemas import (
    SurveySubmission,
)
from ..storage import (
    save_survey,
    get_consent,
)
from ..auth import (
    get_current_user,
)
from ..config import get_settings

from fastapi import APIRouter

logger = logging.getLogger("cyberlab")
settings = get_settings()
router = APIRouter()


@router.post("/api/modules/{module_id}/surveys")
@router.post("/api/surveys/responses")
async def submit_survey_alt(module_id: str = "default", submission: SurveySubmission = None, payload: dict = None, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    
    if not get_consent(user_id):
        raise HTTPException(
            status_code=403, 
            detail="Debe aceptar el consentimiento informado antes de responder encuestas."
        )

    if submission is None and payload is not None:
        sub = SurveySubmission(
            student_id=user_id,
            module_id=payload.get("module_id", module_id),
            responses=payload.get("answers", payload.get("responses", {})),
            rating=payload.get("rating"),
            comments=payload.get("comments", "")
        )
    elif submission is not None:
        sub = submission
        sub.student_id = user_id
        if not sub.module_id:
            sub.module_id = module_id
    else:
        raise HTTPException(status_code=422, detail="Datos de encuesta inválidos")
    
    save_survey(sub)
    return {"status": "ok", "message": "Encuesta guardada exitosamente"}


@router.post("/api/surveys/submit")
async def submit_survey(submission: SurveySubmission, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    submission.student_id = user_id
    
    if not get_consent(user_id):
        raise HTTPException(
            status_code=403, 
            detail="Debe aceptar el consentimiento informado antes de responder encuestas."
        )
        
    save_survey(submission)
    return {"status": "ok", "message": "Encuesta guardada exitosamente"}
