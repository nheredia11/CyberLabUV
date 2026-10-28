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

    model_config = {"populate_by_name": True}


class ModuleDetail(CatalogItem):
    theory: str = ""
    checkpoints: list[CheckpointDef] = Field(default_factory=list)
    survey: list[dict[str, Any]] = Field(default_factory=list, validation_alias=AliasChoices("survey", "surveys", "encuesta"))


class CheckpointSubmission(BaseModel):
    student_id: str = Field(..., validation_alias=AliasChoices("student_id", "user_id"))
    module_id: str = "default"
    checkpoint_id: str
    evidence: str = ""
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


class StudentDashboard(BaseModel):
    student_id: str = Field(..., validation_alias=AliasChoices("student_id", "user_id"))
    progress_percent: float = Field(0.0, validation_alias=AliasChoices("progress_percent", "general_percent"))
    completed_modules_count: int = 0
    total_modules_count: int = 0
    modules: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


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
    student_id: str = Field(..., validation_alias=AliasChoices("student_id", "user_id"))
    module_id: str
    responses: dict[str, Any] = Field(default_factory=dict, validation_alias=AliasChoices("responses", "answers", "answers_json"))
    rating: int | None = None
    comments: str = ""

    model_config = {"populate_by_name": True}


class ScenarioActionRequest(BaseModel):
    user_id: str | None = Field(None, validation_alias=AliasChoices("user_id", "student_id"))
    action: str | None = None

    model_config = {"populate_by_name": True}