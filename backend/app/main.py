from __future__ import annotations

import logging
from fastapi import FastAPI, HTTPException, Request, Response, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .schemas import (
    GoogleLoginRequest,
    StudentDashboard,
    CatalogItem,
    ModuleDetail,
    CheckpointSubmission,
    SurveySubmission,
    ScenarioActionResponse,
)
from .content import get_catalog, get_module_detail
from .storage import get_student_dashboard, record_checkpoint_submission, save_survey

logger = logging.getLogger("cyberlab")

app = FastAPI(title="CyberLabUV API")

# Configurar CORS para permitir peticiones del Frontend (Vite en puerto 5173 / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- AUTENTICACIÓN ---
@app.post("/api/auth/google")
async def google_login(payload: GoogleLoginRequest):
    # Devuelve una sesión exitosa / token simulado o real
    return {
        "status": "ok",
        "user_id": "6472bc6ba01d",
        "email": "estudiante@uv.edu.co",
        "role": "student",
        "token": "mock-jwt-token-cyberlab",
    }


# --- MÓDULOS Y CATÁLOGO ---
@app.get("/api/modules", response_model=list[CatalogItem])
@app.get("/api/catalog", response_model=list[CatalogItem])
async def list_modules():
    return get_catalog()


@app.get("/api/modules/{module_id}", response_model=ModuleDetail)
@app.get("/api/catalog/{module_id}", response_model=ModuleDetail)
async def get_module(module_id: str, user_id: str = ""):
    detail = get_module_detail(module_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Módulo {module_id} no encontrado")
    return detail


# --- ESTUDIANTES Y DASHBOARD ---
@app.get("/api/students/{student_id}/dashboard", response_model=StudentDashboard)
async def get_dashboard(student_id: str):
    dashboard = get_student_dashboard(student_id)
    if not dashboard:
        # Devuelve dashboard por defecto si es nuevo usuario
        return StudentDashboard(
            student_id=student_id,
            progress_percent=0.0,
            completed_modules_count=0,
            total_modules_count=len(get_catalog()),
            modules=[],
        )
    return dashboard


# --- ENTREGAS Y ENCUESTAS ---
@app.post("/api/checkpoints/submit")
async def submit_checkpoint(submission: CheckpointSubmission):
    result = record_checkpoint_submission(submission)
    return {"status": "ok", "result": result}


@app.post("/api/surveys/submit")
async def submit_survey(submission: SurveySubmission):
    save_survey(submission)
    return {"status": "ok", "message": "Encuesta guardada exitosamente"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}