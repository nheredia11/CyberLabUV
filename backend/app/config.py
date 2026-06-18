from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración central del backend local de CyberLab."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = Field(default="CyberLab", alias="PROJECT_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_port: int = Field(default=8000, alias="API_PORT")
    platform_port: int = Field(default=8080, alias="PLATFORM_PORT")
    database_path: str = Field(default="data/cyberlabuv.db", alias="DATABASE_PATH")
    cyberlab_root: Path | None = Field(default=None, alias="CYBERLAB_ROOT")
    allow_scenario_commands: bool = Field(default=False, alias="ALLOW_SCENARIO_COMMANDS")
    dev_token: str = Field(default="cyberlabuv-local-token", alias="DEV_TOKEN")

    # Se deja como texto para evitar errores de Pydantic al leer listas desde .env
    cors_origins_raw: str = Field(
        default="http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Permite leer CORS_ORIGINS como lista JSON o como texto separado por comas."""
        raw_value = self.cors_origins_raw.strip()

        if not raw_value:
            return []

        if raw_value.startswith("["):
            try:
                values = json.loads(raw_value)
                return [str(item).strip() for item in values if str(item).strip()]
            except json.JSONDecodeError:
                pass

        return [item.strip() for item in raw_value.split(",") if item.strip()]

    @property
    def root_dir(self) -> Path:
        if self.cyberlab_root:
            return self.cyberlab_root.resolve()
        return Path(__file__).resolve().parents[2]

    @property
    def platform_dir(self) -> Path:
        return self.root_dir / "platform"

    @property
    def modules_dir(self) -> Path:
        return self.platform_dir / "modules"

    @property
    def scenario_catalog_path(self) -> Path:
        return self.platform_dir / "scenario_catalog.json"

    @property
    def absolute_database_path(self) -> Path:
        db_path = Path(self.database_path)
        if db_path.is_absolute():
            return db_path
        return self.root_dir / db_path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()