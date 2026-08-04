from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .auth import verify_google_token
from .config import get_settings
from .content import ContentError, clear_content_cache, load_all_modules, load_catalog, load_module
from .scenario_runner import run_scenario_action, run_terminal_command
from .schemas import (
    CatalogItem,
    GoogleLoginRequest,
    ModuleDetail,
    ScenarioActionResponse,
    StudentDashboard,
    StudentModuleProgress,
    SurveySubmission,
    TeacherAnalytics,
    CheckpointPayload,
    CheckpointSubmission,
)
from .storage import (
    get_student_dashboard,
    get_student_module_progress,
    get_teacher_analytics,
    init_db,
    save_survey,
    save_checkpoint,
)

settings = get_settings()

# PRIORIDAD 3: Diccionario de sesiones activas en memoria (Inicia vacío en producción)
ACTIVE_SESSIONS: dict[str, dict] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="CyberLab API",
    description="Backend local para módulos, checkpoints y orquestación controlada de escenarios.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_current_user(x_cyberlab_token: str = Header(default="")) -> dict:
    """Verifica el token recibido en la cabecera y retorna los datos del usuario."""
    if x_cyberlab_token in ACTIVE_SESSIONS:
        return ACTIVE_SESSIONS[x_cyberlab_token]

    # PRIORIDAD 3: Puerta temporal estricta solo para desarrollo/testing local
    if settings.app_env == "development":
        if x_cyberlab_token == settings.dev_token:
            return {
                "id": "dev-user",
                "email": "dev@correounivalle.edu.co",
                "role": "student",
            }
        if x_cyberlab_token == "dev-teacher-token":
            return {
                "id": "profesor-local",
                "email": "profesor@correounivalle.edu.co",
                "role": "teacher",
            }
        if x_cyberlab_token == "dev-student-token":
            return {
                "id": "estudiante-local",
                "email": "estudiante@correounivalle.edu.co",
                "role": "student",
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesión no válida o token ausente.",
    )


def require_teacher_role(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependencia que restringe el acceso exclusivamente a usuarios con rol docente."""
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requieren privilegios de docente.",
        )
    return current_user


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "project": settings.project_name,
        "environment": settings.app_env,
        "scenario_commands_enabled": settings.allow_scenario_commands,
    }


@app.get("/api/modules", response_model=list[CatalogItem])
def list_modules() -> list[CatalogItem]:
    try:
        return load_catalog()
    except ContentError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/modules/{module_id}", response_model=ModuleDetail)
def get_module(module_id: str) -> ModuleDetail:
    try:
        return load_module(module_id)
    except ContentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/admin/content/reload", dependencies=[Depends(require_teacher_role)])
def reload_content_cache() -> dict[str, str]:
    clear_content_cache()
    return {"status": "ok", "message": "Caché de contenidos recargada."}


@app.post("/api/surveys/responses", dependencies=[Depends(get_current_user)])
def submit_survey(submission: SurveySubmission) -> dict[str, str]:
    valid_modules = {module.id for module in load_all_modules()}
    if submission.module_id.upper() not in valid_modules:
        raise HTTPException(status_code=404, detail="Módulo no encontrado.")
    save_survey(submission)
    return {"status": "ok", "message": "Encuesta registrada."}


# PRIORIDAD 2: Endpoint para registrar los checkpoints persistidos en SQLite
@app.post(
    "/api/students/{student_id}/modules/{module_id}/checkpoints",
    dependencies=[Depends(get_current_user)],
)
def submit_checkpoint_endpoint(student_id: str, module_id: str, payload: CheckpointPayload) -> dict[str, str]:
    # payload.answers debe ser un dict {"checkpoint_id": "evidencia"}
    for cp_id, evidence in payload.answers.items():
        submission = CheckpointSubmission(
            user_id=student_id,
            student_id=student_id,
            module_id=module_id,
            checkpoint_id=cp_id,
            evidence=evidence,
            status="pending_review",
            feedback=""
        )
        save_checkpoint(submission)
        
    return {"status": "success", "message": "Evidencias guardadas en SQLite"}


class TerminalCommandRequest(BaseModel):
    user_id: str
    scenario_id: str
    command: str


@app.post(
    "/api/scenarios/{scenario_id}/command",
    response_model=ScenarioActionResponse,
    dependencies=[Depends(get_current_user)],
)
def terminal_command(
    scenario_id: str, payload: TerminalCommandRequest
) -> ScenarioActionResponse:
    allowed, returncode, stdout, stderr, message = run_terminal_command(
        scenario_id, payload.command
    )
    return ScenarioActionResponse(
        scenario_id=scenario_id.upper(),
        action="command",
        allowed=allowed,
        returncode=returncode,
        stdout=stdout[-4000:] if stdout else "",
        stderr=stderr[-4000:] if stderr else "",
        message=message,
    )


@app.post("/api/auth/google")
def google_login(payload: GoogleLoginRequest) -> dict:
    try:
        user = verify_google_token(payload.credential)
        session_token = f"session-{user['id']}"
        ACTIVE_SESSIONS[session_token] = user
        return {
            "user": user,
            "token": session_token,
        }
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Error validando Google: {str(exc)}"
        ) from exc


@app.get(
    "/api/students/{student_id}/dashboard",
    response_model=StudentDashboard,
    dependencies=[Depends(get_current_user)],
)
def student_dashboard(student_id: str) -> StudentDashboard:
    return get_student_dashboard(student_id)


@app.get(
    "/api/teacher/analytics",
    response_model=TeacherAnalytics,
    dependencies=[Depends(require_teacher_role)],
)
def teacher_analytics() -> TeacherAnalytics:
    return get_teacher_analytics()


@app.post(
    "/api/scenarios/{scenario_id}/{action}",
    response_model=ScenarioActionResponse,
    dependencies=[Depends(get_current_user)],
)
def scenario_action(scenario_id: str, action: str) -> ScenarioActionResponse:
    allowed, returncode, stdout, stderr, message = run_scenario_action(
        scenario_id, action
    )
    return ScenarioActionResponse(
        scenario_id=scenario_id.upper(),
        action=action.lower(),
        allowed=allowed,
        returncode=returncode,
        stdout=stdout[-4000:],
        stderr=stderr[-4000:],
        message=message,
    )


@app.get(
    "/api/students/{student_id}/modules/{module_id}/progress",
    response_model=StudentModuleProgress,
    dependencies=[Depends(get_current_user)],
)
def student_module_progress(
    student_id: str, module_id: str
) -> StudentModuleProgress:
    try:
        return get_student_module_progress(student_id, module_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# PRIORIDAD 7: Implementación del endpoint adaptativo de feedback faltante
@app.get(
    "/api/modules/{module_id}/feedback",
    dependencies=[Depends(get_current_user)],
)
def get_module_feedback(module_id: str, student_id: str) -> dict[str, str]:
    # Traemos el progreso real de la BD
    progress = get_student_module_progress(student_id, module_id)
    
    if not progress or progress.progress_percent == 0:
        return {
            "level": "Inicial", 
            "message": "Inicia la práctica y guarda tus primeros checkpoints para recibir orientación."
        }
    
    if progress.progress_percent >= 100:
        return {
            "level": "Autónomo", 
            "message": "¡Excelente! Has dominado el escenario por completo y validado todos tus hallazgos."
        }
        
    return {
        "level": "En consolidación",
        "message": f"Vas por buen camino. Has completado {progress.checkpoints_completed} checkpoint(s). Continúa extrayendo evidencia de la terminal."
    }