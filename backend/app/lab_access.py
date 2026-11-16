"""Acceso web a los laboratorios a través del backend (proxy inverso).

Cada laboratorio se publica en /labs/<sesión>/ en el mismo origen que la API. Así:
- funciona desde cualquier lugar (detrás de un único HTTPS), no solo en 127.0.0.1;
- solo el dueño de la sesión puede abrirlo (enlace firmado de un solo uso + cookie);
- no hace falta exponer puertos de los laboratorios en el servidor.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import socket
import time
from typing import Any

from .config import get_settings

logger = logging.getLogger("cyberlab")

TICKET_TTL_SECONDS = 120
COOKIE_PREFIX = "cyberlab_lab_"


# ---------------------------------------------------------------- firmas -------------

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign(payload: dict[str, Any]) -> str:
    body = _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    mac = hmac.new(get_settings().lab_link_secret.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(mac)}"


def verify(token: str, *, kind: str, session_id: str) -> dict[str, Any] | None:
    """Devuelve el contenido si la firma es válida, del tipo y sesión esperados y no venció."""
    try:
        body, mac = token.split(".", 1)
        expected = hmac.new(get_settings().lab_link_secret.encode(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(mac)):
            return None
        payload = json.loads(_unb64(body))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("k") != kind or payload.get("sid") != session_id:
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload


def make_ticket(user_id: str, session_id: str) -> str:
    return sign({"k": "ticket", "uid": user_id, "sid": session_id, "exp": int(time.time()) + TICKET_TTL_SECONDS})


def make_cookie(user_id: str, session_id: str, expires_at: float) -> str:
    return sign({"k": "cookie", "uid": user_id, "sid": session_id, "exp": int(expires_at)})


def lab_path(session_id: str) -> str:
    return f"/labs/{session_id}/"


# ------------------------------------------------------- red del laboratorio ---------

def running_in_container() -> bool:
    return os.path.exists("/.dockerenv")


def edge_network(project_name: str, scenario_slug: str) -> str:
    """Red no interna del laboratorio (el atacante nunca está en ella)."""
    return f"{project_name}_{scenario_slug}_edge"


def own_container_id() -> str:
    return get_settings().backend_container or socket.gethostname()
