from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

Role = Literal["student", "teacher"]
CheckpointStatus = Literal["pending", "done", "review"]

class LoginRequest(BaseModel):
    email: str

class GoogleLoginRequest(BaseModel):
    credential: str

class User(BaseModel):
    id: str
    name: str
    email: str
    role: Role
    avatar: str | None = None

class CheckpointSubmissionIn(BaseModel):
    user_id: str = "ana"
    checkpoint_id: str
    status: CheckpointStatus = "done"
    evidence: str | None = Field(default=None, max_length=2000)

class SurveyIn(BaseModel):
    user_id: str = "ana"
    answers: dict[str, Any]
    rating: int | None = Field(default=None, ge=1, le=5)
    comments: str | None = Field(default=None, max_length=2500)

class TeacherNoteIn(BaseModel):
    teacher_id: str = "carlos"
    student_id: str = "ana"
    module_id: str
    body: str = Field(min_length=3, max_length=2500)

class ScenarioActionIn(BaseModel):
    user_id: str = "ana"
    scenario_id: str
    action: Literal["start", "stop", "reset", "status"]

class TerminalCommandIn(BaseModel):
    user_id: str = "ana"
    scenario_id: str
    command: str = Field(min_length=2, max_length=500)

class ApiMessage(BaseModel):
    status: str
    message: str
    data: dict[str, Any] | None = None
