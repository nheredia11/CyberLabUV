from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
# Agregar junto a los otros imports de arriba
from .auth import verify_google_token
from .schemas import GoogleLoginRequest

from .config import get_settings
from .content import ContentError, clear_content_cache, load_all_modules, load_catalog, load_module
from .schemas import (
    CatalogItem,
    CheckpointSubmission,
    ModuleDetail,
    ScenarioActionResponse,
    StudentDashboard,
    StudentModuleProgress,
    SurveySubmission,
    TeacherAnalytics,
)
from .scenario_runner import run_scenario_action
from .storage import (
    get_student_dashboard,
    get_student_module_progress,
    get_teacher_analytics,
    init_db,
    save_checkpoint,
    save_survey,
)

# Modifica tus imports actuales para que luzcan así:
from pydantic import BaseModel # Asegúrate de importar BaseModel
from .scenario_runner import run_scenario_action, run_terminal_command

settings = get_settings()


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


def require_dev_token(x_cyberlab_token: str = Header(default="")) -> None:
    if x_cyberlab_token != settings.dev_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token local inválido o ausente.",
        )


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


@app.post("/api/admin/content/reload", dependencies=[Depends(require_dev_token)])
def reload_content_cache() -> dict[str, str]:
    clear_content_cache()
    return {"status": "ok", "message": "Caché de contenidos recargada."}


@app.post("/api/progress/checkpoints", dependencies=[Depends(require_dev_token)])
def submit_checkpoint(submission: CheckpointSubmission) -> dict[str, str]:
    valid_modules = {module.id for module in load_all_modules()}
    if submission.module_id.upper() not in valid_modules:
        raise HTTPException(status_code=404, detail="Módulo no encontrado.")
    save_checkpoint(submission)
    return {"status": "ok", "message": "Checkpoint registrado."}


@app.post("/api/surveys/responses", dependencies=[Depends(require_dev_token)])
def submit_survey(submission: SurveySubmission) -> dict[str, str]:
    valid_modules = {module.id for module in load_all_modules()}
    if submission.module_id.upper() not in valid_modules:
        raise HTTPException(status_code=404, detail="Módulo no encontrado.")
    save_survey(submission)
    return {"status": "ok", "message": "Encuesta registrada."}

# --- AÑADIR CERCA DE LA LÍNEA 115 EN main.py ---

class TerminalCommandRequest(BaseModel):
    user_id: str
    scenario_id: str
    command: str

@app.post("/api/scenarios/{scenario_id}/command", response_model=ScenarioActionResponse, dependencies=[Depends(require_dev_token)])
def terminal_command(scenario_id: str, payload: TerminalCommandRequest) -> ScenarioActionResponse:
    allowed, returncode, stdout, stderr, message = run_terminal_command(scenario_id, payload.command)
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
        return {
            "user": user,
            "token": f"google-session-{user['id']}",
        }
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error validando Google: {str(exc)}") from exc


@app.get("/api/students/{student_id}/dashboard", response_model=StudentDashboard, dependencies=[Depends(require_dev_token)])
def student_dashboard(student_id: str) -> StudentDashboard:
    return get_student_dashboard(student_id)


@app.get("/api/teacher/analytics", response_model=TeacherAnalytics, dependencies=[Depends(require_dev_token)])
def teacher_analytics() -> TeacherAnalytics:
    return get_teacher_analytics()


@app.post("/api/scenarios/{scenario_id}/{action}", response_model=ScenarioActionResponse, dependencies=[Depends(require_dev_token)])
def scenario_action(scenario_id: str, action: str) -> ScenarioActionResponse:
    allowed, returncode, stdout, stderr, message = run_scenario_action(scenario_id, action)
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
    dependencies=[Depends(require_dev_token)],
)
def student_module_progress(student_id: str, module_id: str) -> StudentModuleProgress:
    try:
        return get_student_module_progress(student_id, module_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

def validate_institutional_email(email: str) -> str:
    normalized_email = email.strip().lower()

    if "@" not in normalized_email:
        raise HTTPException(
            status_code=400,
            detail="El correo no tiene un formato válido.",
        )

    domain = normalized_email.rsplit("@", 1)[1]
    allowed_domains = set(settings.google_allowed_domains)

    if domain not in allowed_domains:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Solo cuentas institucionales. "
                f"Dominio recibido: {domain}. "
                f"Permitidos: {', '.join(sorted(allowed_domains))}"
            ),
        )

    return normalized_email