from __future__ import annotations

import os
import uuid
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)

ACTIVE_SESSIONS: dict[str, dict[str, Any]] = {}


def create_session(user_id: str, role: str, email: str = "") -> str:
  token = str(uuid.uuid4())
  ACTIVE_SESSIONS[token] = {
      "user_id": user_id,
      "role": role,
      "email": email,
  }
  return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
  if not credentials:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Falta el encabezado de autorización",
    )

  token = credentials.credentials
  user_session = ACTIVE_SESSIONS.get(token)

  if not user_session:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de sesión inválido o no registrado",
    )

  return user_session


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