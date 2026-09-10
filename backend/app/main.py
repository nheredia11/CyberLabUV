from __future__ import annotations

import logging
from typing import Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    GoogleLoginRequest,
    StudentDashboard,
    CatalogItem,
    ModuleDetail,
    CheckpointSubmission,
    SurveySubmission,
)
from .content import load_catalog, load_module
from .storage import save_checkpoint, get_student_dashboard, save_survey
from .auth import get_current_user, require_teacher_role, is_dev_login_enabled

logger = logging.getLogger("cyberlab")

app = FastAPI(title="CyberLabUV API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- HEALTH CHECK ---
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# --- AUTENTICACIÓN ---
@app.post("/api/auth/google")
async def google_login(payload: GoogleLoginRequest):
    return {
        "status": "ok",
        "user_id": "6472bc6ba01d",
        "email": "estudiante@uv.edu.co",
        "role": "student",
        "token": "student-6472bc6ba01d",
    }


@app.post("/api/auth/dev-login")
async def dev_login(role: str = "teacher"):
    if not is_dev_login_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El inicio de sesión de desarrollo está deshabilitado.",
        )
    return {
        "status": "ok",
        "user_id": "dev_user",
        "role": role,
        "token": f"{role}-dev_user",
    }


# --- MÓDULOS Y CATÁLOGO ---
@app.get("/api/modules", response_model=list[CatalogItem])
@app.get("/api/catalog", response_model=list[CatalogItem])
async def list_modules():
    return load_catalog()


@app.get("/api/modules/{module_id}", response_model=ModuleDetail)
@app.get("/api/catalog/{module_id}", response_model=ModuleDetail)
async def get_module(module_id: str):
    detail = load_module(module_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Módulo {module_id} no encontrado")
    return detail


# --- ESTUDIANTES Y DASHBOARD ---
@app.get("/api/students/{student_id}/dashboard", response_model=StudentDashboard)
async def get_dashboard(student_id: str):
    dashboard = get_student_dashboard(student_id)
    if not dashboard:
        catalog = load_catalog()
        return StudentDashboard(
            student_id=student_id,
            progress_percent=0.0,
            completed_modules_count=0,
            total_modules_count=len(catalog),
            modules=[],
        )
    return dashboard


# --- ENTREGAS Y ENCUESTAS ---
@app.post("/api/checkpoints/submit")
async def submit_checkpoint(submission: CheckpointSubmission):
    result = save_checkpoint(submission)
    return {"status": "ok", "result": result}


@app.post("/api/surveys/submit")
async def submit_survey(submission: SurveySubmission):
    save_survey(submission)
    return {"status": "ok", "message": "Encuesta guardada exitosamente"}


# --- RUTAS DE DOCENTE (PROTEGIDAS) ---
@app.get("/api/teacher/analytics")
async def get_teacher_analytics(
    teacher: dict[str, Any] = Depends(require_teacher_role),
):
    return {"status": "ok", "teacher_id": teacher["user_id"], "analytics": {}}