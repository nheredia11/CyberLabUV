from pydantic import BaseModel, Field, model_validator, AliasChoices
from typing import Optional, List, Dict, Any

# ==============================================================================
# AUTENTICACIÓN
# ==============================================================================

class GoogleLoginRequest(BaseModel):
    credential: str


# ==============================================================================
# CATÁLOGO Y MÓDULOS (/api/modules)
# ==============================================================================

class Checkpoint(BaseModel):
    id: str
    title: Optional[str] = Field(default="Checkpoint", validation_alias=AliasChoices("title", "titulo"))
    titulo: Optional[str] = None
    description: Optional[str] = ""
    points: Optional[int] = 10
    hint: Optional[str] = None
    type: Optional[str] = "text"
    question: Optional[str] = ""

class CheckpointDef(Checkpoint):
    """Alias de compatibilidad para cargadores de contenido."""
    pass

class CatalogItem(BaseModel):
    id: str
    title: Optional[str] = "Módulo CyberLab"
    titulo: Optional[str] = None
    description: Optional[str] = "Módulo de laboratorio práctico."
    difficulty: Optional[str] = "Intermedio"
    category: Optional[str] = "Ciberseguridad"
    duration: Optional[str] = "30 mins"
    duration_minutes: Optional[int] = 30
    ruta: Optional[str] = ""
    checkpoints_count: Optional[int] = 0
    completed: Optional[bool] = False

    @model_validator(mode="before")
    @classmethod
    def sync_spanish_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "titulo" in values and not values.get("title"):
                values["title"] = values["titulo"]
            if "title" in values and not values.get("titulo"):
                values["titulo"] = values["title"]
            if "ruta" not in values:
                values["ruta"] = values.get("id", "")
        return values

class ModuleDetail(BaseModel):
    id: str
    title: Optional[str] = "Detalle del Módulo"
    description: Optional[str] = ""
    difficulty: Optional[str] = "Intermedio"
    category: Optional[str] = "Ciberseguridad"
    orden: Optional[int] = 0
    checkpoints: List[Checkpoint] = []
    guide_markdown: Optional[str] = ""
    theory_markdown: Optional[str] = ""
    survey: Optional[Dict[str, Any]] = None
    catalog: Optional[CatalogItem] = None


# ==============================================================================
# CHECKPOINTS Y PROGRESO DE ESTUDIANTES
# ==============================================================================

class CheckpointPayload(BaseModel):
    checkpoint_id: Optional[str] = ""
    user_id: Optional[str] = "default_user"
    student_id: Optional[str] = None
    module_id: Optional[str] = ""
    status: str = "completed"
    evidence: Optional[str] = ""
    completed: Optional[bool] = None
    answers: Optional[Dict[str, Any]] = None

class CheckpointSubmission(BaseModel):
    user_id: Optional[str] = "default_user"
    student_id: Optional[str] = None
    module_id: str
    checkpoint_id: Optional[str] = ""
    evidence: Optional[str] = ""
    status: str = "completed"
    completed: Optional[bool] = None
    answers: Optional[Dict[str, Any]] = None

    @property
    def is_completed(self) -> bool:
        if self.completed is not None:
            return self.completed
        return str(self.status).lower() in ["completed", "done", "aprobado", "true", "1"]

class CheckpointProgressRecord(BaseModel):
    user_id: str
    module_id: str
    checkpoint_id: str
    status: str = "completed"
    evidence: Optional[str] = ""
    completed: bool = True
    updated_at: Optional[str] = None

class ModuleFeedbackResponse(BaseModel):
    module_id: str
    student_id: str
    completed_checkpoints: List[str] = []
    total_checkpoints: int = 0
    progress_percentage: float = 0.0
    level_message: str = ""

class StudentModuleProgress(BaseModel):
    user_id: str
    module_id: str
    checkpoints: List[Dict[str, Any]] = []
    completed: bool = False

class StudentDashboard(BaseModel):
    user_id: Optional[str] = "default_user"
    student_id: Optional[str] = None
    total_checkpoints_completed: int = 0
    checkpoints_completed: Optional[int] = 0
    checkpoints_total: Optional[int] = 0
    modules_total: Optional[int] = 0
    modules_started: Optional[int] = 0
    progress_percent: Optional[float] = 0.0
    general_percent: Optional[float] = 0.0
    modules_progress: Dict[str, Any] = {}
    modules: Optional[List[Any]] = []
    updated_at: Optional[Any] = None

    def __getitem__(self, item: str) -> Any:
        """Permite acceso estilo diccionario (ej: dashboard['total_checkpoints_completed'])."""
        return getattr(self, item)

    @model_validator(mode="before")
    @classmethod
    def sync_dashboard_fields(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if "student_id" in values and not values.get("user_id"):
                values["user_id"] = values["student_id"]
            if "user_id" in values and not values.get("student_id"):
                values["student_id"] = values["user_id"]
            if "total_checkpoints_completed" in values and not values.get("checkpoints_completed"):
                values["checkpoints_completed"] = values["total_checkpoints_completed"]
            if "checkpoints_completed" in values and not values.get("total_checkpoints_completed"):
                values["total_checkpoints_completed"] = values["checkpoints_completed"]
            if "progress_percent" in values and not values.get("general_percent"):
                values["general_percent"] = values["progress_percent"]
            if "general_percent" in values and not values.get("progress_percent"):
                values["progress_percent"] = values["general_percent"]
        return values
class TeacherAnalytics(BaseModel):
    total_students: int = 0
    active_labs: int = 0
    students: List[Dict[str, Any]] = []

class SurveySubmission(BaseModel):
    user_id: str
    module_id: str
    responses: Dict[str, Any] = {}


# ==============================================================================
# ACCIONES EN ESCENARIOS Y TERMINAL
# ==============================================================================

class ScenarioActionRequest(BaseModel):
    scenario_id: Optional[str] = ""
    action: str = ""
    command: Optional[str] = ""

class ScenarioActionPayload(BaseModel):
    scenario_id: str = ""
    action: str = ""
    command: str = ""

class TerminalCommandPayload(BaseModel):
    scenario_id: str = ""
    command: str = ""

class ScenarioActionResponse(BaseModel):
    status: str = "success"
    scenario_id: Optional[str] = ""
    action: Optional[str] = ""
    message: Optional[str] = ""
    output: Optional[str] = ""