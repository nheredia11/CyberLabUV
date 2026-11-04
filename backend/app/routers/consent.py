"""Rutas: consent."""
from __future__ import annotations

import logging
from fastapi import Depends


from ..storage import (
    get_consent,
    save_consent,
)
from ..auth import (
    get_current_user,
)
from ..config import get_settings

from fastapi import APIRouter

logger = logging.getLogger("cyberlab")
settings = get_settings()
router = APIRouter()


@router.get("/api/consent")
async def check_consent(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    consent = get_consent(user_id)
    return {"accepted": consent is not None, "consent": consent}


@router.post("/api/consent")
async def submit_consent(payload: dict, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user_id")
    version = payload.get("version", "1.0")
    result = save_consent(user_id, version)
    return {"status": "ok", **result}
