from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CatalogItem(BaseModel):
    id: str
    titulo: str
    tipo: str
    estado: str
    nivel: str
    frameworks: list[str] = Field(default_factory=list)
    duracion_estimada: str | None = None
    ruta: str


class Checkpoint(BaseModel):
    id: str
    titulo: str
    tipo: Literal["confirmacion", "texto"]
    evidencia: str


class SurveyQuestion(BaseModel):
    id: str
    pregunta: str
    tipo: str


class ModuleDetail(BaseModel):
    id: str
    titulo: str
    orden: int
    descripcion: str
    objetivos: list[str] = Field(default_factory=list)
    encuesta_obligatoria: bool = True
    checkpoints_obligatorios: bool = True
    comando_inicio: str | None = None
    theory_markdown: str
    checkpoints: list[Checkpoint]
    survey: list[SurveyQuestion]
    catalog: CatalogItem | None = None


class CheckpointSubmission(BaseModel):
    student_id: str = Field(min_length=2)
    module_id: str = Field(min_length=2)
    checkpoint_id: str = Field(min_length=2)
    evidence: str = Field(default="", max_length=3000)
    completed: bool = True


class SurveySubmission(BaseModel):
    student_id: str = Field(min_length=2)
    module_id: str = Field(min_length=2)
    answers: dict[str, Any] = Field(default_factory=dict)


class ScenarioActionResponse(BaseModel):
    scenario_id: str
    action: str
    allowed: bool
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    message: str


class StudentDashboard(BaseModel):
    student_id: str
    modules_total: int
    modules_started: int
    checkpoints_completed: int
    checkpoints_total: int
    progress_percent: float
    updated_at: datetime


class TeacherAnalytics(BaseModel):
    modules_total: int
    students_total: int
    checkpoints_completed: int
    checkpoints_total: int
    average_progress_percent: float
    updated_at: datetime

class CheckpointProgressRecord(BaseModel):
    student_id: str
    module_id: str
    checkpoint_id: str
    evidence: str
    completed: bool
    updated_at: datetime


class StudentModuleProgress(BaseModel):
    student_id: str
    module_id: str
    checkpoints_completed: int
    checkpoints_total: int
    progress_percent: float
    checkpoints: list[CheckpointProgressRecord]