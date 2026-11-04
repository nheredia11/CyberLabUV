from __future__ import annotations

from typing import Any
from pydantic import AliasChoices, BaseModel, Field


class CatalogItem(BaseModel):
    id: str
    title: str = Field(..., validation_alias=AliasChoices("title", "titulo"))
    description: str = Field("", validation_alias=AliasChoices("description", "descripcion"))
    category: str = "general"
    difficulty: str = "beginner"
    estimated_hours: int = 1
    route: str = Field("", validation_alias=AliasChoices("route", "ruta", "path"))
    active: bool = True
    orden: int = Field(0, validation_alias=AliasChoices("orden", "order"))

    model_config = {"populate_by_name": True}

    @property
    def ruta(self) -> str:
        return self.route

    @property
    def order(self) -> int:
        return self.orden


class CheckpointDef(BaseModel):
    id: str
    title: str = Field(..., validation_alias=AliasChoices("title", "titulo", "evidencia"))
    type: str = Field("flag", validation_alias=AliasChoices("type", "tipo"))
    question: str = Field("", validation_alias=AliasChoices("question", "evidencia", "titulo"))
    points: int = 10
    completed: bool = False  # se rellena por estudiante en GET /api/modules/{id}

    model_config = {"populate_by_name": True}


class ModuleDetail(CatalogItem):
    theory: str = ""
    checkpoints: list[CheckpointDef] = Field(default_factory=list)
    survey: list[dict[str, Any]] = Field(default_factory=list, validation_alias=AliasChoices("survey", "surveys", "encuesta"))
    survey_completed: bool = False  # se rellena por estudiante en GET /api/modules/{id}


class CheckpointSubmission(BaseModel):
    student_id: str = Field(..., max_length=100, validation_alias=AliasChoices("student_id", "user_id"))
    module_id: str = Field("default", max_length=50)
    checkpoint_id: str = Field(..., max_length=100)
    evidence: str = Field("", max_length=5000)
    status: str = Field("done", validation_alias=AliasChoices("status", "completed"))

    model_config = {"populate_by_name": True}


CheckpointPayload = CheckpointSubmission


class CheckpointProgressRecord(BaseModel):
    student_id: str = Field(..., validation_alias=AliasChoices("student_id", "user_id"))
    module_id: str = ""
    checkpoint_id: str
    status: str = Field("done", validation_alias=AliasChoices("status", "completed"))
    points: int = 0
    completed_at: str = ""

    model_config = {"populate_by_name": True}


class StudentModuleProgress(BaseModel):
    student_id: str = Field(..., validation_alias=AliasChoices("student_id", "user_id"))
    module_id: str
    progress_percent: float = Field(0.0, validation_alias=AliasChoices("progress_percent", "general_percent"))
    completed_checkpoints: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class ModuleProgressView(BaseModel):
    percent: float = 0.0
    completed_checkpoints: int = 0
    total_checkpoints: int = 0
    survey_completed: bool = False


class DashboardModule(BaseModel):
    id: str
    title: str
    description: str = ""
    orden: int = 0
    progress: ModuleProgressView


class StudentDashboard(BaseModel):
    """Vista del progreso que consumen Dashboard y Resultados en el frontend."""

    student_id: str
    general_percent: float = 0.0
    completed_modules: int = 0
    total_modules: int = 0
    points: int = 0   # suma de los puntos de cada checkpoint completado
    badges: int = 0   # una insignia por módulo completado (regla provisional)
    modules: list[DashboardModule] = Field(default_factory=list)


class TeacherAnalytics(BaseModel):
    total_students: int = 0
    average_progress_percent: float = Field(
        0.0, validation_alias=AliasChoices("average_progress_percent", "general_percent")
    )
    students_progress: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., validation_alias=AliasChoices("credential", "id_token"))


class SurveySubmission(BaseModel):
    student_id: str = Field(..., max_length=100, validation_alias=AliasChoices("student_id", "user_id"))
    module_id: str = Field(..., max_length=50)
    responses: dict[str, Any] = Field(default_factory=dict, max_length=100, validation_alias=AliasChoices("responses", "answers", "answers_json"))
    # Promedio Likert (1 a 5) calculado por la interfaz; puede ser decimal (p. ej. 4.33).
    rating: float | None = Field(None, ge=1, le=5)
    comments: str = Field("", max_length=2000)

    model_config = {"populate_by_name": True}


class ScenarioActionRequest(BaseModel):
    user_id: str | None = Field(None, validation_alias=AliasChoices("user_id", "student_id"))
    action: str | None = None

    model_config = {"populate_by_name": True}


class ScenarioCommandRequest(BaseModel):
    scenario_id: str
    command: str


class LoginDemoRequest(BaseModel):
    email: str
    role: str = "student"
    name: str = ""


class ScenarioCommandResponse(BaseModel):
    """Respuesta de POST /api/scenarios/{id}/command. La salida viaja en `output`."""
    status: str
    output: str


class ScenarioActionResponse(BaseModel):
    """Respuesta de start/stop/status/reset de un escenario."""
    scenario_id: str
    action: str
    status: str
    message: str
    local_url: str | None = None
    session_id: str | None = None


class SurveyModuleMetric(BaseModel):
    module_id: str
    responses: int
    avg_rating: float | None = None


class SurveyMetricsResponse(BaseModel):
    status: str
    total_responses: int
    modules: list[SurveyModuleMetric]


class TeacherNoteRequest(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=100)
    module_id: str = Field("general", max_length=50)
    body: str = Field(..., min_length=1, max_length=5000)


class StatusMessageResponse(BaseModel):
    status: str
    message: str
