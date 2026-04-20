from __future__ import annotations

from fastapi import APIRouter

from ..models import CrisprDesignRequest, RefineGrnaRequest

router = APIRouter(tags=["crispr"])


@router.post("/crispr-design")
def crispr_design(body: CrisprDesignRequest):
    """
    Design gRNA candidates for a given SNP.

    NOT YET IMPLEMENTED — returns an empty candidate list with a status message.
    CRISPR design logic will be added in a future milestone.
    """
    return {
        "grnaCandidates": [],
        "snp": body.snp,
        "windowSize": body.windowSize,
        "status": "not_implemented",
        "message": (
            "CRISPR guide RNA design is not yet implemented. "
            "This endpoint will return scored gRNA candidates once the design logic is added."
        ),
    }


@router.post("/refine-grna")
def refine_grna(body: RefineGrnaRequest):
    """
    Refine an existing gRNA to a new length and re-score it.

    NOT YET IMPLEMENTED — returns a stub response.
    """
    return {
        "refined": None,
        "originalSequence": body.grnaSequence,
        "requestedLength": body.newLength,
        "status": "not_implemented",
        "message": (
            "gRNA refinement is not yet implemented. "
            "This endpoint will return a re-scored, length-adjusted guide once the logic is added."
        ),
    }
