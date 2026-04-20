from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..paths import BLAST_ROOT  # also ensures BLAST_ROOT is on sys.path
from blast_database import inspect_database

from ..config import NOT_CONFIGURED_DETAIL, get_settings
from ..models import BindingSiteRequest

router = APIRouter(tags=["binding"])


@router.post("/binding-site")
def get_binding_site(body: BindingSiteRequest):
    """
    NOT YET IMPLEMENTED — binding site computation will be added in a future milestone.
    """
    return {
        "bindingSite": None,
        "grna": body.grna,
        "snp": body.snp,
        "windowSize": body.windowSize,
        "status": "not_implemented",
        "message": (
            "Binding site computation is not yet implemented. "
            "This endpoint will return strand, PAM, and cut-site coordinates once the logic is added."
        ),
    }


@router.get("/reference-info")
def get_reference_info():
    """Return metadata about the currently loaded BLAST reference database."""
    settings = get_settings()
    if not settings.get("configured"):
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    try:
        return inspect_database(
            blast_bin=settings["blast_bin"],
            db_name=settings["db_name"],
            workdir=settings["workdir"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
