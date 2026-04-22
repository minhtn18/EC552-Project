from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from ..paths import BLAST_ROOT  # also ensures BLAST_ROOT is on sys.path
from Blast_code import add_sequence_to_blast_database, normalize_sequence

from ..config import NOT_CONFIGURED_DETAIL, get_settings, is_configured
from ..models import SequenceRecord

router = APIRouter(tags=["sequences"])

METADATA_PATH = BLAST_ROOT / "blast_database" / "sequence_metadata.json"


def _load_metadata() -> List[dict]:
    try:
        return json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_metadata(records: List[dict]) -> None:
    METADATA_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")


@router.get("/sequences")
def get_sequences():
    return _load_metadata()


@router.post("/sequences", response_model=SequenceRecord, status_code=201)
def add_sequence(body: SequenceRecord):
    """
    Persist a new sequence to both the metadata sidecar and the BLAST database.
    blast_bin must be configured because adding to the BLAST DB rebuilds index files.
    """
    if not is_configured():
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    try:
        cleaned = normalize_sequence(body.sequence)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    records = _load_metadata()
    new_id = max((r.get("id", 0) for r in records), default=0) + 1

    new_record = {
        "id": new_id,
        "name": body.name.strip(),
        "gene": body.gene.strip(),
        "organism": body.organism.strip(),
        "length": len(cleaned),
        "description": (body.description or "").strip(),
        "sequence": cleaned,
        "added": body.added or date.today().isoformat(),
    }

    settings = get_settings()
    blast_result = add_sequence_to_blast_database(
        header=body.name.strip(),
        sequence=cleaned,
        db_name=settings["db_name"],
        blast_bin=settings["blast_bin"],
        workdir=Path(settings["workdir"]),
    )

    build = blast_result.get("build_result")
    if build and build.returncode != 0:
        detail = (build.stderr or "").strip() or "makeblastdb failed."
        raise HTTPException(status_code=500, detail=f"BLAST DB update failed: {detail}")

    records.append(new_record)
    _save_metadata(records)
    return SequenceRecord(**new_record)
