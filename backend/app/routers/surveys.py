"""Rutas: encuestas del piloto.

Las tres rutas guardan lo mismo; la interfaz usa /api/modules/{id}/surveys.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..content import load_module
from ..schemas import StatusMessageResponse, SurveySubmission
from ..storage import get_consent, save_survey

router = APIRouter()


def _store_survey(submission: SurveySubmission, current_user: dict) -> dict:
    user_id = current_user["user_id"]
    if not get_consent(user_id):
        raise HTTPException(
            status_code=403,
            detail="Debe aceptar el consentimiento informado antes de responder encuestas.",
        )
    module = load_module(submission.module_id)
    if not module:
        raise HTTPException(status_code=422, detail=f"Módulo {submission.module_id} no existe.")

    # La identidad sale del token, nunca del cuerpo de la petición.
    submission.student_id = user_id
    submission.module_id = module.id
    save_survey(submission)
    return {"status": "ok", "message": "Encuesta guardada exitosamente"}


@router.post("/api/modules/{module_id}/surveys", response_model=StatusMessageResponse)
async def submit_module_survey(module_id: str, submission: SurveySubmission, current_user: dict = Depends(get_current_user)):
    submission.module_id = module_id  # la ruta manda sobre el cuerpo
    return _store_survey(submission, current_user)


@router.post("/api/surveys/responses", response_model=StatusMessageResponse)
@router.post("/api/surveys/submit", response_model=StatusMessageResponse)
async def submit_survey(submission: SurveySubmission, current_user: dict = Depends(get_current_user)):
    return _store_survey(submission, current_user)
