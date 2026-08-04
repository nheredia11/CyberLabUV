from __future__ import annotations
import hashlib
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .config import get_settings

def verify_google_token(credential: str) -> dict:
    settings = get_settings()

    payload = id_token.verify_oauth2_token(
        credential,
        google_requests.Request(),
        settings.google_client_id,
        clock_skew_in_seconds=30,
    )

    email = (payload.get("email") or "").lower().strip()
    name = payload.get("name") or email.split("@")[0]
    picture = payload.get("picture", "")

    if not payload.get("email_verified", False):
        raise PermissionError("El correo de Google no está verificado.")

    domain = email.split("@")[-1]
    allowed = [d.lower().strip() for d in settings.google_allowed_domains]
    if domain not in allowed:
        raise PermissionError(
            f"Solo cuentas institucionales. Dominio recibido: {domain}. "
            f"Permitidos: {', '.join(allowed)}"
        )

    user_id = hashlib.sha1(email.encode()).hexdigest()[:12]
    avatar = "".join(p[0] for p in name.split()[:2]).upper() or "UV"

    # CORRECCIÓN PRIORIDAD 1: El rol ya no se decide en el frontend.
    # El backend verifica si el email autenticado está en la lista de profesores permitidos (.env)
    role = "teacher" if email in settings.teacher_emails else "student"

    return {
        "id": user_id,
        "email": email,
        "name": name,
        "avatar": avatar,
        "picture": picture,
        "role": role,
    }