from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..paths import BLAST_ROOT  # ensures BLAST_ROOT is on sys.path before crispr_logic import
from blast_database import inspect_database
from ..crispr_logic import compute_binding_site

from ..config import NOT_CONFIGURED_DETAIL, get_settings, is_configured
from ..models import BindingSiteRequest, BindingSiteResponse

router = APIRouter(tags=["binding"])


@router.post("/binding-site", response_model=BindingSiteResponse)
def get_binding_site(body: BindingSiteRequest):
    """
    Locate the guide RNA in the reference database, extract a genomic window
    of body.windowSize bases, and return the coordinates needed by the SVG
    binding viewer: gRNA bind start/end, PAM start/end, SNP position in window,
    and cut site position. Also returns both DNA strands.
    """
    if not is_configured():
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    settings = get_settings()
    grna = body.grna
    snp  = body.snp

    guide_seq  = str(grna.get("sequence", ""))
    strand     = str(grna.get("strand", "sense"))
    snp_pos    = int(snp.get("position", 0))
    window_size = int(body.windowSize or 100)

    if not guide_seq:
        raise HTTPException(status_code=422, detail="grna.sequence is required.")

    try:
        result = compute_binding_site(
            guide_sequence=guide_seq,
            strand=strand,
            snp_position=snp_pos,
            blast_bin=settings["blast_bin"],
            db_name=settings["db_name"],
            workdir=Path(settings["workdir"]),
            window_size=window_size,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Guide sequence '{guide_seq}' could not be located in the reference database. "
                "The guide may have been designed from a patient sequence that differs from the reference."
            ),
        )

    return BindingSiteResponse(**result)


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
