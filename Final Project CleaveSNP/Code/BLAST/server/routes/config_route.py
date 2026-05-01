from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..config import get_settings, save_config
from ..models import ConfigRequest, ConfigResponse

router = APIRouter(tags=["config"])


@router.get("/config", response_model=ConfigResponse)
def get_config():
    """Return the current server configuration, including auto-computed workdir and db_name."""
    return get_settings()


@router.post("/config", response_model=ConfigResponse)
def set_config(body: ConfigRequest):
    """
    Save the blast_bin path to server_config.json.
    workdir and db_name are always auto-computed — they are not accepted from the caller.
    """
    blast_bin = body.blast_bin.strip()
    if not blast_bin:
        raise HTTPException(status_code=400, detail="blast_bin cannot be empty.")

    if not Path(blast_bin).exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {blast_bin}")

    return save_config({"blast_bin": blast_bin})
