from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración central de CyberLab.

    Soporta variables antiguas y nuevas del proyecto:
    - CYBERLAB_DB / DATABASE_PATH
    - GOOGLE_CLIENT_ID / VITE_GOOGLE_CLIENT_ID
    - GOOGLE_ALLOWED_DOMAINS como texto separado por comas
    - TEACHER_EMAILS como texto separado por comas (Fuente de verdad de roles)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    project_name: str = Field(default="CyberLab", alias="PROJECT_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")

    api_port: int = Field(default=8000, alias="API_PORT")
    platform_port: int = Field(default=8080, alias="PLATFORM_PORT")

    cyberlab_root: Path | None = Field(default=None, alias="CYBERLAB_ROOT")

    database_path: str = Field(
        default="data/cyberlabuv.sqlite3",
        validation_alias=AliasChoices("CYBERLAB_DB", "DATABASE_PATH"),
    )

    allow_scenario_commands: bool = Field(
        default=False,
        alias="ALLOW_SCENARIO_COMMANDS",
    )

    dev_token: str = Field(
        default="cyberlabuv-local-token",
        alias="DEV_TOKEN",
    )

    cors_origins_raw: str = Field(
        default=(
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:8080,"
            "http://127.0.0.1:8080"
        ),
        alias="CORS_ORIGINS",
    )

    google_client_id: str = Field(
        default="",
        validation_alias=AliasChoices("GOOGLE_CLIENT_ID", "VITE_GOOGLE_CLIENT_ID"),
    )

    google_allowed_domains_raw: str = Field(
        default="correounivalle.edu.co,univalle.edu.co,uv.edu.co",
        alias="GOOGLE_ALLOWED_DOMAINS",
    )

    # NUEVO: Campo para leer los correos autorizados como docentes
    teacher_emails_raw: str = Field(
        default="",
        alias="TEACHER_EMAILS",
    )

    @property
    def cors_origins(self) -> list[str]:
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
    def google_allowed_domains(self) -> list[str]:
        """Dominios permitidos como lista real.

        Importante: no devolver el string crudo, porque si se hace set(string)
        se obtienen caracteres individuales: c, o, r, r, e...
        """
        raw_value = self.google_allowed_domains_raw.strip()

        if not raw_value:
            return []

        if raw_value.startswith("["):
            try:
                values = json.loads(raw_value)
                return [
                    str(item).strip().lower()
                    for item in values
                    if str(item).strip()
                ]
            except json.JSONDecodeError:
                pass

        return [
            item.strip().lower()
            for item in raw_value.split(",")
            if item.strip()
        ]

    @property
    def google_allowed_domain_list(self) -> list[str]:
        return self.google_allowed_domains

    # NUEVO: Propiedad para obtener los correos de docentes como lista limpia
    @property
    def teacher_emails(self) -> list[str]:
        """Correos autorizados como docentes."""
        raw_value = self.teacher_emails_raw.strip()
        
        if not raw_value:
            return []
            
        if raw_value.startswith("["):
            try:
                values = json.loads(raw_value)
                return [str(item).strip().lower() for item in values if str(item).strip()]
            except json.JSONDecodeError:
                pass
                
        return [item.strip().lower() for item in raw_value.split(",") if item.strip()]

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