from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
import os

class Settings(BaseModel):
    app_name: str = "CyberLabUV"
    app_slug: str = "cyberlabuv"
    environment: str = os.getenv("APP_ENV", "development")
    api_prefix: str = "/api"
    project_root: Path = Path(os.getenv("CYBERLAB_ROOT", Path(__file__).resolve().parents[2]))
    database_path: Path = Path(os.getenv("CYBERLAB_DB", Path(__file__).resolve().parents[2] / "data" / "cyberlabuv.sqlite3"))
    allow_scenario_commands: bool = os.getenv("ALLOW_SCENARIO_COMMANDS", "false").lower() == "true"
    cors_origins: list[str] = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")]

    @property
    def modules_dir(self) -> Path:
        return self.project_root / "platform" / "modules"

    @property
    def catalog_path(self) -> Path:
        return self.project_root / "platform" / "scenario_catalog.json"

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    return settings
