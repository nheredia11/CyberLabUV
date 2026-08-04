from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from pydantic import AliasChoices

# --- Modelos del Catálogo y Contenido ---
class ModuleProgressInfo(BaseModel):
    percent: int = 0
    completed_checkpoints: int = 0
    total_checkpoints: int = 0
    survey_completed: bool = False


class CatalogItem(BaseModel):
    id: str
    titulo: str = Field(validation_alias=AliasChoices("title", "titulo"))
    descripcion: str = Field(default="", validation_alias=AliasChoices("description", "descripcion"))
    ruta: str = Field(default="", validation_alias=AliasChoices("ruta", "path"))
    orden: int = Field(default=0, validation_alias=AliasChoices("orden", "order"))
    duration_minutes: int = Field(default=60)
    difficulty: str = Field(default="Intermedio")
    tags: list[str] = Field(default_factory=list)
    progress: ModuleProgressInfo | None = None


class CheckpointDef(BaseModel):
    id: str
    type: str = Field(default="flag", validation_alias=AliasChoices("type", "tipo"))
    question: str = Field(default="", validation_alias=AliasChoices("question", "pregunta", "titulo", "title"))
    hint: str | None = Field(default=None, validation_alias=AliasChoices("hint", "pista", "descripcion", "description"))


class SectionDef(BaseModel):
    id: str
    title: str
    content: str


class ModuleDetail(CatalogItem):
    teoria: list[SectionDef] = Field(default_factory=list, alias="theory")
    practica: list[SectionDef] = Field(default_factory=list, alias="practice")
    checkpoints: list[CheckpointDef] = Field(default_factory=list)


# --- Modelos de Autenticación ---
class GoogleLoginRequest(BaseModel):
    credential: str


# --- Modelos de Dashboard Estudiante ---
class StudentDashboard(BaseModel):
    student_id: str
    modules_total: int
    modules_started: int
    checkpoints_completed: int
    general_percent: float
    modules: list[CatalogItem] = Field(default_factory=list)


class StudentModuleProgress(BaseModel):
    module_id: str
    checkpoints_completed: int
    total_checkpoints: int
    progress_percent: float
    is_completed: bool
    survey_completed: bool
    answers: dict[str, str] = Field(default_factory=dict)


# --- Modelos de Eventos de Escenarios ---
class ScenarioActionResponse(BaseModel):
    scenario_id: str
    action: str
    allowed: bool
    returncode: int | None
    stdout: str
    stderr: str
    message: str


# --- Modelos de Encuesta ---
class SurveySubmission(BaseModel):
    student_id: str
    module_id: str
    rating: int = Field(ge=1, le=5)
    clarity: int = Field(ge=1, le=5)
    difficulty: int = Field(ge=1, le=5)
    comments: str | None = None


# --- NUEVOS MODELOS (PRIORIDAD 2 y 5) ---
class CheckpointPayload(BaseModel):
    module_id: str
    student_id: str
    answers: dict[str, str]


class FeedbackPayload(BaseModel):
    student_id: str
    module_id: str
    feedback: str


class CheckpointSubmission(BaseModel):
    user_id: str
    student_id: str
    module_id: str
    checkpoint_id: str
    evidence: str
    status: str = "pending_review"
    feedback: str = ""

# --- MODELO FALTANTE RESTAURADO ---
class CheckpointProgressRecord(BaseModel):
    student_id: str
    module_id: str
    checkpoint_id: str
    evidence: str
    status: str
    updated_at: datetime


# --- Modelos de Analíticas para Docentes ---
class TeacherModuleStat(BaseModel):
    module_id: str
    active_students: int
    completion_rate: float
    avg_score: float | None = None


class TeacherAnalytics(BaseModel):
    total_students: int
    active_modules: int
    overall_completion: float
    modules: list[TeacherModuleStat] = Field(default_factory=list)