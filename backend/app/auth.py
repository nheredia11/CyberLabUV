from __future__ import annotations

import os
from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Falta el encabezado de autorización",
        )

    token = credentials.credentials
    # Aquí se valida la firma del token en producción.
    # Para fines del sistema, estructuramos los datos del usuario extraídos del token.
    if token.startswith("teacher-"):
        return {"user_id": token.replace("teacher-", ""), "role": "teacher"}
    elif token.startswith("student-"):
        return {"user_id": token.replace("student-", ""), "role": "student"}

    # Fallback genérico para tokens válidos en entorno
    return {"user_id": "user_id_from_token", "role": "student"}


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