"""Rutas: auth."""
from __future__ import annotations

import logging
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials


from ..schemas import (
    GoogleLoginRequest,
)
from ..auth import (
    is_dev_login_enabled,
    create_session,
    revoke_session,
    security,
)
from ..services import get_or_create_google_user
from ..config import get_settings

from fastapi import APIRouter
from ..ratelimit import check_rate_limit
from ..schemas import LoginDemoRequest

logger = logging.getLogger("cyberlab")
settings = get_settings()
router = APIRouter()


@router.post("/api/auth/login")
async def login_demo(payload: LoginDemoRequest):
    if not is_dev_login_enabled():
        raise HTTPException(status_code=403, detail="El login de desarrollo/demo está deshabilitado.")
    
    settings = get_settings()
    email = payload.email.lower().strip()
    user_id = email.split("@")[0] if email else "demo-user"
    
    configured_teachers = getattr(settings, "teacher_emails", ["dev@uv.edu.co", "docente@uv.edu.co"])
    teacher_emails = [e.lower().strip() for e in configured_teachers]
    
    role = "teacher" if email in teacher_emails else "student"
    name = payload.name or ("Docente Demo" if role == "teacher" else "Estudiante Demo")
    
    token = create_session(user_id=user_id, role=role, email=email)
    user_data = {
        "id": user_id,
        "user_id": user_id,
        "email": email,
        "role": role,
        "name": name,
        "avatar": name[:2].upper()
    }
    return {
        "status": "ok",
        "user_id": user_id,
        "email": email,
        "role": role,
        "token": token,
        "user": user_data
    }


@router.post("/api/auth/google")
async def google_login(payload: GoogleLoginRequest, request: Request):
    # Aplicar rate limit de 30/min por IP
    check_rate_limit("google_auth", 30)(request)
    try:
        user_info = get_or_create_google_user(payload.credential)
        token = create_session(user_id=user_info["id"], role=user_info["role"], email=user_info["email"])
        user_data = {
            "id": user_info["id"],
            "user_id": user_info["id"],
            "email": user_info["email"],
            "role": user_info["role"],
            "name": user_info.get("name"),
            "avatar": user_info.get("avatar")
        }
        return {
            "status": "ok",
            "user_id": user_info["id"],
            "email": user_info["email"],
            "role": user_info["role"],
            "token": token,
            "name": user_info.get("name"),
            "avatar": user_info.get("avatar"),
            "user": user_data
        }
    except Exception as e:
        logger.exception("Error de autenticación con Google: %s", e)
        raise HTTPException(status_code=401, detail="Error de autenticación con Google.")


@router.post("/api/auth/dev-login")
async def dev_login(role: str = "teacher"):
    if not is_dev_login_enabled():
        raise HTTPException(status_code=403, detail="El login de desarrollo está deshabilitado.")
    email = "dev@uv.edu.co" if role == "teacher" else "estudiante@uv.edu.co"
    user_id = email.split("@")[0]
    token = create_session(user_id=user_id, role=role, email=email)
    user_data = {"id": user_id, "user_id": user_id, "email": email, "role": role, "name": "Dev User", "avatar": "DU"}
    return {"status": "ok", "user_id": user_id, "role": role, "token": token, "user": user_data}


@router.post("/api/auth/logout")
def logout(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials:
        revoke_session(credentials.credentials)
    return {"success": True, "message": "Sesión cerrada correctamente"}
