from __future__ import annotations

from typing import Any
from pydantic import AliasChoices, BaseModel, Field


class CatalogItem(BaseModel):
    id: str
    title: str = Field(..., validation_alias=AliasChoices("title", "titulo"))
    description: str = ""
    category: str = "general"
    difficulty: str = "beginner"
    estimated_hours: int = 1
    route: str = Field("", validation_alias=AliasChoices("route", "ruta", "path"))
    active: bool = True

    model_config = {"populate_by_name": True}


class CheckpointDef(BaseModel):
    id: str
    title: str = Field(..., validation_alias=AliasChoices("title", "titulo"))
    type: str = "flag"
    question: str = ""
    points: int = 10

    model_config = {"populate_by_name": True}


class ModuleDetail(CatalogItem):
    checkpoints: list[CheckpointDef] = Field(default_factory=list)


class CheckpointSubmission(BaseModel):
    student_id: str = Field(..., validation_alias=AliasChoices("student_id", "user_id"))
    checkpoint_id: str
    evidence: str = ""
    status: str = Field("done", validation_alias=AliasChoices("status", "completed"))

    model_config = {"populate_by_name": True}


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
    credential: str


class SurveySubmission(BaseModel):
    student_id: str = Field(..., validation_alias=AliasChoices("student_id", "user_id"))
    module_id: str
    responses: dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class ScenarioActionResponse(BaseModel):
    status: str
    message: str = ""
    scenario_id: str = ""