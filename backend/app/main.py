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
from .auth import (
    get_current_user,
    require_teacher_role,
    is_dev_login_enabled,
    create_session,
)

from pydantic import BaseModel
from typing import Optional

from .scenario_runner import start_scenario_session, stop_scenario_session
from .database import init_db   # o como se llame tu función de inicialización

import asyncio
from contextlib import asynccontextmanager
from .cleanup import start_cleanup_scheduler, cleanup_expired_sessions
from .database import init_db

logger = logging.getLogger("cyberlab")

app = FastAPI(title="CyberLabUV API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScenarioActionRequest(BaseModel):
    user_id: str
    action: str          # "start" o "stop"
    
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    init_db()
    
    # Limpieza inicial por si el servidor se reinició con sesiones huérfanas
    await cleanup_expired_sessions()
    
    # Tarea en segundo plano cada 5 minutos
    cleanup_task = asyncio.create_task(start_cleanup_scheduler(interval_seconds=300))
    
    yield
    
    # --- SHUTDOWN ---
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="CyberLabUV API",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
  return {"status": "healthy"}


@app.post("/api/auth/google")
async def google_login(payload: GoogleLoginRequest):
  user_id = "6472bc6ba01d"
  email = "estudiante@uv.edu.co"
  role = "student"
  token = create_session(user_id=user_id, role=role, email=email)
  return {
      "status": "ok",
      "user_id": user_id,
      "email": email,
      "role": role,
      "token": token,
  }


@app.post("/api/auth/dev-login")
async def dev_login(role: str = "teacher"):
  if not is_dev_login_enabled():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="El inicio de sesión de desarrollo está deshabilitado.",
    )
  user_id = "dev_user"
  token = create_session(user_id=user_id, role=role, email="dev@uv.edu.co")
  return {
      "status": "ok",
      "user_id": user_id,
      "role": role,
      "token": token,
  }


@app.get("/api/modules", response_model=list[CatalogItem])
@app.get("/api/catalog", response_model=list[CatalogItem])
async def list_modules():
  return load_catalog()


@app.get("/api/modules/{module_id}", response_model=ModuleDetail)
@app.get("/api/catalog/{module_id}", response_model=ModuleDetail)
async def get_module(module_id: str):
  detail = load_module(module_id)
  if not detail:
    raise HTTPException(
        status_code=404, detail=f"Módulo {module_id} no encontrado"
    )
  return detail


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


@app.post("/api/checkpoints/submit")
async def submit_checkpoint(submission: CheckpointSubmission):
  result = save_checkpoint(submission)
  return {"status": "ok", "result": result}


@app.post("/api/surveys/submit")
async def submit_survey(submission: SurveySubmission):
  save_survey(submission)
  return {"status": "ok", "message": "Encuesta guardada exitosamente"}


@app.get("/api/teacher/analytics")
async def get_teacher_analytics(
    teacher: dict[str, Any] = Depends(require_teacher_role),
):
  return {"status": "ok", "teacher_id": teacher["user_id"], "analytics": {}}

@app.post("/api/scenarios/{scenario_id}/action")
async def handle_scenario_action(scenario_id: str, payload: ScenarioActionRequest):
    """
    Inicia o detiene un escenario de forma aislada por estudiante.
    """
    action = payload.action.lower().strip()
    user_id = payload.user_id

    if action == "start":
        success, message, data = await start_scenario_session(
            user_id=user_id,
            scenario_id=scenario_id,
        )

        if not success:
            raise HTTPException(status_code=500, detail=message)

        return {
            "status": "success",
            "message": message,
            "scenario_id": scenario_id.upper(),
            "session_id": data.get("session_id"),
            "local_url": data.get("local_url"),
            "docker_project_name": data.get("docker_project_name"),
            "assigned_ports": data.get("assigned_ports"),
        }

    elif action in ("stop", "down"):
        success, message = await stop_scenario_session(
            user_id=user_id,
            scenario_id=scenario_id,
        )

        if not success:
            raise HTTPException(status_code=500, detail=message)

        return {
            "status": "success",
            "message": message,
            "scenario_id": scenario_id.upper(),
        }

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Acción no soportada: {payload.action}. Usa 'start' o 'stop'."
        )