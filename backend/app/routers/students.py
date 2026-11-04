"""Rutas: students."""
from __future__ import annotations

import logging
from fastapi import HTTPException, Depends
from fastapi.responses import Response


from ..schemas import (
    StudentDashboard,
)
from ..content import load_all_modules
from ..storage import (
    get_student_dashboard,
)
from ..auth import (
    get_current_user,
)
from ..database import utcnow
from ..config import get_settings

from fastapi import APIRouter

logger = logging.getLogger("cyberlab")
settings = get_settings()
from ..dashboard import build_student_dashboard
from ..reports import build_student_report_pdf

router = APIRouter()


@router.get("/api/students/{student_id}/dashboard", response_model=StudentDashboard)
async def get_dashboard(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher" and current_user.get("user_id") != student_id:
        raise HTTPException(status_code=403, detail="No autorizado para acceder a este dashboard")
    
    return build_student_dashboard(student_id)


@router.get("/api/students/{student_id}/report")
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


@router.get("/api/students/{student_id}/report.pdf")
async def get_student_report_pdf(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "teacher" and current_user.get("user_id") != student_id:
        raise HTTPException(status_code=403, detail="No autorizado")

    dashboard = get_student_dashboard(student_id)
    all_modules = load_all_modules()

    pdf_bytes = build_student_report_pdf(student_id, dashboard, all_modules)
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=reporte_{student_id}.pdf"}
    )
