"""Rutas: health."""
from __future__ import annotations

import logging


from ..config import get_settings

from fastapi import APIRouter

logger = logging.getLogger("cyberlab")
settings = get_settings()
router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy"}
