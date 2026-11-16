"""Rutas: acceso web a los laboratorios (proxy inverso por el backend).

Flujo:
1. La interfaz pide POST /api/scenarios/{id}/lab-link con el token del estudiante.
2. Recibe /labs/<sesión>/?ticket=<firma de un solo uso, 2 min> y lo abre en una pestaña.
3. El backend valida el ticket, deja una cookie HttpOnly limitada a /labs/<sesión>/ y
   redirige a la misma ruta sin el ticket. Desde ahí, cada petición se reenvía al laboratorio.
"""
from __future__ import annotations

import logging
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response

from ..auth import get_current_user
from ..config import get_settings
from ..database import get_active_session, get_session_by_id
from ..lab_access import COOKIE_PREFIX, lab_path, make_cookie, make_ticket, verify
from ..scenario_runner import SCENARIOS, resolve_lab_target
from ..schemas import LabLinkResponse

logger = logging.getLogger("cyberlab")
router = APIRouter()

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer",
    "transfer-encoding", "upgrade", "host", "content-length", "cookie", "authorization",
}
MAX_BODY = 1_000_000


@router.post("/api/scenarios/{scenario_id}/lab-link", response_model=LabLinkResponse)
async def create_lab_link(scenario_id: str, current_user: dict = Depends(get_current_user)):
    scenario = SCENARIOS.get(scenario_id.upper())
    if not scenario:
        raise HTTPException(status_code=404, detail="Escenario no encontrado")
    active = get_active_session(current_user["user_id"], scenario.slug)
    if not active:
        raise HTTPException(status_code=409, detail="Inicia el escenario antes de abrir el laboratorio.")
    ticket = make_ticket(current_user["user_id"], active["id"])
    return {"lab_url": f"{lab_path(active['id'])}?ticket={ticket}", "expires_in": 120}


def _running_session(session_id: str) -> dict:
    session = get_session_by_id(session_id)
    if not session or session["status"] != "running":
        raise HTTPException(status_code=404, detail="La sesión del laboratorio no existe o ya terminó.")
    return session


@router.api_route(
    "/labs/{session_id}/{path:path}",
    methods=["GET", "POST", "HEAD"],
    include_in_schema=False,
)
async def lab_proxy(session_id: str, path: str, request: Request):
    session = _running_session(session_id)
    cookie_name = f"{COOKIE_PREFIX}{session_id}"
    secure = get_settings().secure_cookies

    # 1) Canje del ticket de un solo uso por una cookie de la sesión
    ticket = request.query_params.get("ticket")
    if ticket:
        payload = verify(ticket, kind="ticket", session_id=session_id)
        if not payload or payload["uid"] != session["user_id"]:
            raise HTTPException(status_code=403, detail="Enlace inválido o vencido. Vuelve a abrir el laboratorio desde la plataforma.")
        expires = datetime.fromisoformat(session["expires_at"]).timestamp()
        resp = RedirectResponse(lab_path(session_id) + path, status_code=303)
        resp.set_cookie(
            cookie_name, make_cookie(session["user_id"], session_id, expires),
            path=lab_path(session_id), httponly=True, samesite="lax", secure=secure,
            max_age=max(int(expires - datetime.now().timestamp()), 60),
        )
        return resp

    # 2) Cada petición debe traer la cookie del dueño de la sesión
    token = request.cookies.get(cookie_name, "")
    payload = verify(token, kind="cookie", session_id=session_id)
    if not payload or payload["uid"] != session["user_id"]:
        raise HTTPException(status_code=401, detail="Abre el laboratorio desde la plataforma (botón «Abrir aplicación vulnerable»).")

    scenario = next((s for s in SCENARIOS.values() if s.slug == session["scenario_slug"]), None)
    target = await resolve_lab_target(session["docker_project_name"], scenario) if scenario else None
    if not target:
        raise HTTPException(status_code=502, detail="El laboratorio no está disponible. Reinícialo desde la plataforma.")

    body = await request.body()
    if len(body) > MAX_BODY:
        raise HTTPException(status_code=413, detail="Petición demasiado grande.")

    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP_BY_HOP}
    headers["X-Forwarded-Prefix"] = lab_path(session_id).rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            upstream = await client.request(
                request.method, f"{target}/{path}", params=request.query_params, content=body, headers=headers
            )
    except httpx.HTTPError as exc:
        logger.warning("Proxy de laboratorio %s falló: %s", session_id, exc)
        raise HTTPException(status_code=502, detail="El laboratorio no respondió. Espera unos segundos e intenta de nuevo.")

    out_headers = {
        k: v for k, v in upstream.headers.items()
        if k.lower() not in HOP_BY_HOP and k.lower() not in {"content-encoding", "set-cookie"}
    }
    return Response(content=upstream.content, status_code=upstream.status_code, headers=out_headers)


@router.get("/labs/{session_id}", include_in_schema=False)
async def lab_root_redirect(session_id: str, request: Request):
    query = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(lab_path(session_id) + query, status_code=307)
