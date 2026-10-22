from __future__ import annotations

import logging
import asyncio
from typing import Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel

from .schemas import (
    GoogleLoginRequest,
    StudentDashboard,
    CatalogItem,
    ModuleDetail,
    CheckpointSubmission,
    SurveySubmission,
    ScenarioActionRequest,
)
from .content import load_catalog, load_module, load_all_modules
from .storage import (
    save_checkpoint, 
    get_student_dashboard, 
    save_survey,
    get_student_module_progress,
    get_teacher_analytics as get_real_teacher_analytics,
    save_note,
    get_consent,
    save_consent,
)
from .auth import (
    get_current_user,
    require_teacher_role,
    is_dev_login_enabled,
    create_session,
)
from .scenario_runner import start_scenario_session, stop_scenario_session, run_scenario_command
from .database import init_db, utcnow
from .cleanup import start_cleanup_scheduler, cleanup_expired_sessions
from .services import get_or_create_google_user
from .config import get_settings
from fastapi.responses import Response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

logger = logging.getLogger("cyberlab")


class ScenarioCommandRequest(BaseModel):
    scenario_id: str
    command: str
    
class LoginDemoRequest(BaseModel):
    email: str
    role: str = "student"
    name: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await cleanup_expired_sessions()
    cleanup_task = asyncio.create_task(start_cleanup_scheduler(interval_seconds=300))
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="CyberLabUV API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/users")
async def get_users(role: str = "", current_user: dict = Depends(get_current_user)):
    return [
        {"user_id": "6472bc6ba01d", "email": "estudiante@uv.edu.co", "role": "student"},
        {"user_id": "dev_user", "email": "dev@uv.edu.co", "role": "teacher"}
    ]
    
   
@app.post("/api/auth/login")
async def login_demo(payload: LoginDemoRequest):
    if not is_dev_login_enabled():
        raise HTTPException(status_code=403, detail="El login de desarrollo/demo está deshabilitado.")
    
    settings = get_settings()
    email = payload.email.lower().strip()
    user_id = email.split("@")[0] if email else "demo-user"
    
    # REGLA DE SEGURIDAD: El rol se determina por backend según los correos docentes permitidos
    configured_teachers = getattr(settings, "teacher_emails", ["dev@uv.edu.co", "docente@uv.edu.co"])
    teacher_emails = [e.lower().strip() for e in configured_teachers]
    
    role = "teacher" if email in teacher_emails else "student"
    name = payload.name or ("Docente Demo" if role == "teacher" else "Estudiante Demo")
    
    token = create_session(user_id=user_id, role=role, email=email)
    user_data = {
        "id": user_id,
        "user_id": user_id,
        "email": email,
        "role": role,
        "name": name,
        "avatar": name[:2].upper()
    }
    return {
        "status": "ok",
        "user_id": user_id,
        "email": email,
        "role": role,
        "token": token,
        "user": user_data
    }


@app.post("/api/auth/google")
async def google_login(payload: GoogleLoginRequest):
    try:
        user_info = get_or_create_google_user(payload.credential)
        token = create_session(user_id=user_info["id"], role=user_info["role"], email=user_info["email"])
        user_data = {
            "id": user_info["id"],
            "user_id": user_info["id"],
            "email": user_info["email"],
            "role": user_info["role"],
            "name": user_info.get("name"),
            "avatar": user_info.get("avatar")
        }
        return {
            "status": "ok",
            "user_id": user_info["id"],
            "email": user_info["email"],
            "role": user_info["role"],
            "token": token,
            "name": user_info.get("name"),
            "avatar": user_info.get("avatar"),
            "user": user_data
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@app.post("/api/auth/dev-login")
async def dev_login(role: str = "teacher"):
    if not is_dev_login_enabled():
        raise HTTPException(status_code=403, detail="El login de desarrollo está deshabilitado.")
    email = "dev@uv.edu.co" if role == "teacher" else "estudiante@uv.edu.co"
    user_id = email.split("@")[0]
    token = create_session(user_id=user_id, role=role, email=email)
    user_data = {"id": user_id, "user_id": user_id, "email": email, "role": role, "name": "Dev User", "avatar": "DU"}
    return {"status": "ok", "user_id": user_id, "role": role, "token": token, "user": user_data}


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
    
@app.get("/api/modules/{module_id}/feedback")
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

@app.post("/api/modules/{module_id}/surveys")
@app.post("/api/surveys/responses")
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

@app.post("/api/teacher/notes")
async def create_teacher_note(payload: dict, teacher: dict[str, Any] = Depends(require_teacher_role)):
    note_data = {
        "teacher_id": teacher["user_id"],
        "student_id": payload.get("student_id"),
        "module_id": payload.get("module_id", "general"),
        "body": payload.get("body", "")
    }
    saved = save_note(note_data)
    return {"status": "ok", "message": "Nota guardada exitosamente", "note": saved}


@app.get("/api/students/{student_id}/dashboard", response_model=StudentDashboard)
async def get_dashboard(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher" and current_user.get("user_id") != student_id:
        raise HTTPException(status_code=403, detail="No autorizado para acceder a este dashboard")
    
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


@app.get("/api/students/{student_id}/report")
async def get_student_report(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher" and current_user.get("user_id") != student_id:
        raise HTTPException(status_code=403, detail="No autorizado para ver este reporte")
    
    dashboard = get_student_dashboard(student_id)
    all_modules = load_all_modules()
    
    return {
        "student_id": student_id,
        "title": f"Reporte Académico de Evidencias - CyberLabUV",
        "generated_at": utcnow(),
        "dashboard": dashboard,
        "modules": [m.model_dump() for m in all_modules]
    }
    
@app.get("/api/students/{student_id}/report.pdf")
async def get_student_report_pdf(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher" and current_user.get("user_id") != student_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    dashboard = get_student_dashboard(student_id)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(50, 750, f"Reporte Académico de Evidencias - CyberLabUV")
    p.drawString(50, 730, f"Estudiante ID: {student_id}")
    p.drawString(50, 710, f"Progreso General: {dashboard.get('progress_percent', 0)}%")
    
    y = 670
    p.drawString(50, y, "Checkpoints y Actividad:")
    for mod in dashboard.get("modules", []):
        y -= 20
        p.drawString(70, y, f"- Módulo/Checkpoint: {mod.get('checkpoint_id')} [{mod.get('status')}]")
        if y < 100:
            p.showPage()
            y = 750
            
    p.save()
    buffer.seek(0)
    
    return Response(buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=reporte_{student_id}.pdf"})


@app.post("/api/checkpoints/submit")
async def submit_checkpoint(submission: CheckpointSubmission, current_user: dict = Depends(get_current_user)):
    token_user_id = current_user.get("user_id")
    if current_user.get("role") != "teacher":
        submission.student_id = token_user_id

    result = save_checkpoint(submission)
    return {"status": "ok", "result": result}


@app.post("/api/surveys/submit")
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


@app.get("/api/teacher/analytics")
async def get_teacher_analytics(
    teacher: dict[str, Any] = Depends(require_teacher_role),
):
    analytics_data = get_real_teacher_analytics()
    return {"status": "ok", "teacher_id": teacher["user_id"], "analytics": analytics_data}


@app.post("/api/scenarios/{scenario_id}/command")
async def handle_scenario_command(scenario_id: str, payload: ScenarioCommandRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    success, output = await run_scenario_command(
        user_id=user_id,
        scenario_id=scenario_id,
        command=payload.command
    )
    if not success:
        raise HTTPException(status_code=400, detail=output)
    return {"status": "success", "output": output}


@app.post("/api/scenarios/{scenario_id}/{action}")
async def handle_scenario_action(scenario_id: str, action: str, payload: ScenarioActionRequest, current_user: dict = Depends(get_current_user)):
    act = (payload.action or action).lower().strip()
    user_id = current_user.get("user_id")

    if act == "start":
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
    elif act in ("stop", "down"):
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
            detail=f"Acción no soportada: {act}. Usa 'start' o 'stop'."
        )
        
@app.get("/api/consent")
async def check_consent(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    consent = get_consent(user_id)
    return {"accepted": consent is not None, "consent": consent}

@app.post("/api/consent")
async def submit_consent(payload: dict, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    version = payload.get("version", "1.0")
    result = save_consent(user_id, version)
    return {"status": "ok", **result}