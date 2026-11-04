"""Rutas: scenarios."""
from __future__ import annotations

import logging
from fastapi import HTTPException, Depends, Request


from ..auth import (
    get_current_user,
)
from ..database import get_active_session
from ..scenario_runner import SCENARIOS, start_scenario_session, stop_scenario_session, run_scenario_command
from ..config import get_settings

from fastapi import APIRouter
from ..ratelimit import check_user_rate_limit
from ..schemas import ScenarioActionResponse, ScenarioCommandResponse, ScenarioCommandRequest

logger = logging.getLogger("cyberlab")
settings = get_settings()
router = APIRouter()


@router.post("/api/scenarios/{scenario_id}/command", response_model=ScenarioCommandResponse)
async def handle_scenario_command(scenario_id: str, payload: ScenarioCommandRequest, request: Request, current_user: dict = Depends(get_current_user)):
    # Rate limit de 30/min por usuario
    user_id = current_user.get("user_id")
    check_user_rate_limit(f"cmd_{user_id}", 30)(user_id)

    success, output = await run_scenario_command(
        user_id=user_id,
        scenario_id=scenario_id,
        command=payload.command
    )
    if not success:
        raise HTTPException(status_code=400, detail=output)
    return {"status": "success", "output": output}


@router.post("/api/scenarios/{scenario_id}/{action}", response_model=ScenarioActionResponse)
async def handle_scenario_action(scenario_id: str, action: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    action_lower = action.lower()
    
    if action_lower == "start":
        success, message, data = await start_scenario_session(user_id, scenario_id)
        resp = {
            "scenario_id": scenario_id.upper(),
            "action": action,
            "status": "ok" if success else "error",
            "message": message,
        }
        if isinstance(data, dict):
            resp.update(data)
        return resp
    
    elif action_lower == "stop":
        success, message = await stop_scenario_session(user_id, scenario_id)
        return {"scenario_id": scenario_id.upper(), "action": action, "status": "ok" if success else "error", "message": message}
    
    elif action_lower == "status":
        scenario = SCENARIOS.get(scenario_id.upper())
        if not scenario:
            raise HTTPException(status_code=404, detail="Escenario no encontrado")
        active = get_active_session(user_id, scenario.slug)
        if active:
            web_port = active["assigned_ports"].get("web", 8000)
            return {
                "scenario_id": scenario_id.upper(),
                "action": "status",
                "status": "running",
                "message": "Sesión activa encontrada",
                "local_url": f"http://127.0.0.1:{web_port}",
                "session_id": active["id"]
            }
        return {
            "scenario_id": scenario_id.upper(),
            "action": "status",
            "status": "stopped",
            "message": "No hay sesión activa",
            "local_url": None,
            "session_id": None
        }
    
    elif action_lower == "reset":
        await stop_scenario_session(user_id, scenario_id)
        success, message, data = await start_scenario_session(user_id, scenario_id)
        resp = {
            "scenario_id": scenario_id.upper(),
            "action": "reset",
            "status": "ok" if success else "error",
            "message": message,
        }
        if isinstance(data, dict):
            resp.update(data)
        return resp
    
    raise HTTPException(status_code=400, detail=f"Acción no soportada: {action}")
