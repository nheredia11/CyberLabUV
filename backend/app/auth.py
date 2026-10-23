from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import connect, row_to_dict, utcnow

security = HTTPBearer(auto_error=False)


def _init_sessions_table() -> None:
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                email TEXT,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


# Inicializar la tabla de sesiones al cargar el módulo
_init_sessions_table()


def create_session(user_id: str, role: str, email: str = "") -> str:
    token = str(uuid.uuid4())
    now = utcnow()
    # Expiración a las 8 horas
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()

    with connect() as conn:
        conn.execute(
            """
            INSERT INTO sessions (token, user_id, role, email, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (token, user_id, role, email, expires_at, now),
        )
        conn.commit()
    return token


def revoke_session(token: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el encabezado de autorización",
        )

    token = credentials.credentials

    with connect() as conn:
        row = conn.execute(
            "SELECT user_id, role, email, expires_at FROM sessions WHERE token = ?",
            (token,),
        ).fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de sesión inválido o no registrado",
        )

    session_data = row_to_dict(row)

    # Validar expiración (8 horas)
    try:
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            revoke_session(token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de sesión expirado",
            )
    except (ValueError, TypeError):
        pass

    return {
        "user_id": session_data["user_id"],
        "role": session_data["role"],
        "email": session_data.get("email", ""),
    }


def require_teacher_role(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    if current_user.get("role") != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de docente",
        )
    return current_user


def is_dev_login_enabled() -> bool:
    return os.getenv("ENABLE_DEV_LOGIN", "false").lower() in ("true", "1")