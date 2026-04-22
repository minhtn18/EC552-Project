from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..paths import BLAST_ROOT  # ensures BLAST_ROOT is on sys.path before crispr_logic import
from ..crispr_logic import find_grna_candidates, refine_guide
from ..config import NOT_CONFIGURED_DETAIL, get_settings, is_configured
from ..models import (
    CrisprDesignRequest,
    CrisprDesignResponse,
    GrnaCandidate,
    RefineGrnaRequest,
    RefineGrnaResponse,
)

router = APIRouter(tags=["crispr"])


@router.post("/crispr-design", response_model=CrisprDesignResponse)
def crispr_design(body: CrisprDesignRequest):
    """
    Scan surroundingSequence for NGG PAM sites, extract 20-mer guide RNAs,
    score each by GC content / cut-site distance / homopolymer penalty /
    off-target count, and return the top candidates sorted by composite score.
    """
    if not is_configured():
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    settings = get_settings()
    snp = body.snp

    # Derive the SNP's 0-based position within surroundingSequence.
    # The frontend passes snp.position as a 1-based query position; we use it
    # as an approximation relative to the window center when an exact offset
    # is not provided.
    snp_pos_in_window = int(snp.get("position", len(body.surroundingSequence) // 2))

    try:
        candidates = find_grna_candidates(
            surrounding_sequence=body.surroundingSequence,
            snp_position=snp_pos_in_window,
            ref_nucleotide=str(snp.get("refNucleotide", "A")),
            var_nucleotide=str(snp.get("varNucleotide", "T")),
            blast_bin=settings["blast_bin"],
            db_name=settings["db_name"],
            workdir=Path(settings["workdir"]),
            max_candidates=10,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return CrisprDesignResponse(
        grnaCandidates=[GrnaCandidate(**c) for c in candidates]
    )


@router.post("/refine-grna", response_model=RefineGrnaResponse)
def refine_grna(body: RefineGrnaRequest):
    """
    Trim or extend a guide RNA to the requested length and re-score it.
    Returns the adjusted guide alongside the original score and improvement delta.
    """
    if not is_configured():
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    settings = get_settings()

    # Approximate original score from the input sequence alone (no re-blast)
    from ..crispr_logic import _score_guide
    previous_scores = _score_guide(
        guide=body.grnaSequence,
        pam_position=len(body.grnaSequence),
        snp_position=body.snpPosition,
        blast_bin=settings["blast_bin"],
        db_name=settings["db_name"],
        workdir=Path(settings["workdir"]),
    )
    previous_score = previous_scores["score"]

    try:
        refined = refine_guide(
            grna_sequence=body.grnaSequence,
            new_length=body.newLength,
            reference_context=body.referenceContext,
            snp_position=body.snpPosition,
            blast_bin=settings["blast_bin"],
            db_name=settings["db_name"],
            workdir=Path(settings["workdir"]),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if refined is None:
        raise HTTPException(status_code=422, detail="Could not refine guide to the requested length.")

    improvement = round(refined["score"] - previous_score, 4)
    return RefineGrnaResponse(
        refinedGRNA=GrnaCandidate(**refined),
        previousScore=round(previous_score, 4),
        improvement=improvement,
    )
