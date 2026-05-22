from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .content import load_module, load_modules
from .database import init_db
from .schemas import CheckpointSubmissionIn, LoginRequest, ScenarioActionIn, SurveyIn, TeacherNoteIn
from .services import analytics, dashboard, get_user_by_email, list_users, module_progress, run_scenario_action, save_checkpoint, save_note, save_survey

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", description="API académica para el simulador CyberLabUV")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    init_db()

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}

@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict:
    user = get_user_by_email(payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario demo no encontrado")
    return {"user": user, "token": f"demo-token-{user['id']}"}

@app.get("/api/users")
def users(role: str | None = Query(default=None)) -> list[dict]:
    return list_users(role)

@app.get("/api/modules")
def modules() -> list[dict]:
    return load_modules()

@app.get("/api/modules/{module_id}")
def module_detail(module_id: str, user_id: str = Query(default="ana")) -> dict:
    try:
        module = load_module(module_id)
        return {**module, "progress": module_progress(user_id, module_id)}
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Módulo no encontrado") from exc

@app.get("/api/students/{user_id}/dashboard")
def student_dashboard(user_id: str) -> dict:
    return dashboard(user_id)

@app.post("/api/modules/{module_id}/checkpoints")
def checkpoint(module_id: str, payload: CheckpointSubmissionIn) -> dict:
    return save_checkpoint(module_id, payload.model_dump())

@app.post("/api/modules/{module_id}/surveys")
def survey(module_id: str, payload: SurveyIn) -> dict:
    return save_survey(module_id, payload.model_dump())

@app.post("/api/scenarios/action")
def scenario_action(payload: ScenarioActionIn) -> dict:
    return run_scenario_action(payload.user_id, payload.scenario_id, payload.action)

@app.get("/api/teacher/analytics")
def teacher_analytics() -> dict:
    return analytics()

@app.post("/api/teacher/notes")
def teacher_note(payload: TeacherNoteIn) -> dict:
    return save_note(payload.model_dump())
