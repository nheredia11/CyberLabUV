"""Rutas: teacher."""
from __future__ import annotations

import logging
import csv
import io
from typing import Any
from fastapi import Depends
from fastapi.responses import Response


from ..storage import (
    get_teacher_analytics as get_real_teacher_analytics,
    save_note,
    get_pilot_export_data,
)
from ..auth import (
    require_teacher_role,
)
from ..config import get_settings

from fastapi import APIRouter

logger = logging.getLogger("cyberlab")
settings = get_settings()
from ..schemas import TeacherNoteRequest, SurveyMetricsResponse
from ..storage import get_survey_metrics

router = APIRouter()


@router.post("/api/teacher/notes")
async def create_teacher_note(payload: TeacherNoteRequest, teacher: dict[str, Any] = Depends(require_teacher_role)):
    note_data = {
        "teacher_id": teacher["user_id"],
        "student_id": payload.student_id,
        "module_id": payload.module_id,
        "body": payload.body.strip(),
    }
    saved = save_note(note_data)
    return {"status": "ok", "message": "Nota guardada exitosamente", "note": saved}


@router.get("/api/teacher/export.csv")
async def export_teacher_csv(include_comments: bool = False, teacher: dict[str, Any] = Depends(require_teacher_role)):
    """Exporta métricas consolidadas del pilotaje con control de comentarios opcionales."""
    data = get_pilot_export_data(include_comments=include_comments)
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "user_id", "module_id", "checkpoint_id", 
        "checkpoint_status", "first_activity", "last_activity",
        "rating", "answers_json"
    ]
    if include_comments:
        headers.append("comments")
    writer.writerow(headers)

    for row in data:
        row_data = [
            row.get("user_id"),
            row.get("module_id"),
            row.get("checkpoint_id"),
            row.get("checkpoint_status"),
            row.get("first_activity"),
            row.get("last_activity"),
            row.get("rating"),
            row.get("answers_json")
        ]
        if include_comments:
            row_data.append(row.get("comments"))
        writer.writerow(row_data)

    output.seek(0)
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cyberlab_pilot_export.csv"}
    )


@router.get("/api/teacher/analytics")
async def get_teacher_analytics(
    teacher: dict[str, Any] = Depends(require_teacher_role),
):
    analytics_data = get_real_teacher_analytics()
    return {"status": "ok", "teacher_id": teacher["user_id"], "analytics": analytics_data}


@router.get("/api/teacher/survey-metrics", response_model=SurveyMetricsResponse)
async def get_teacher_survey_metrics(teacher: dict[str, Any] = Depends(require_teacher_role)):
    """Métricas reales de las encuestas del piloto, por módulo."""
    data = get_survey_metrics()
    return {"status": "ok", **data}
