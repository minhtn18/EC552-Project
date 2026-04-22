from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ..paths import BLAST_ROOT  # also ensures BLAST_ROOT is on sys.path
from Blast_code import (
    add_fasta_to_blast_database,
    build_blast_database_from_fasta_text,
    fetch_all_blast_records,
    parse_fasta_text,
)

from ..config import NOT_CONFIGURED_DETAIL, get_settings, is_configured
from ..models import DbBuildRequest, DbBuildResponse, DbClearResponse, DbStatusResponse

router = APIRouter(prefix="/database", tags=["database"])

_DB_FILE_EXTENSIONS = (".nhr", ".ndb")


def _db_exists(db_name: str) -> bool:
    db_path = Path(db_name)
    return any(
        (db_path.parent / f"{db_path.name}{ext}").exists()
        for ext in _DB_FILE_EXTENSIONS
    )


def _db_status_dict() -> dict:
    """Build a DbStatusResponse-shaped dict from the current database state."""
    settings = get_settings()
    db_name: str = settings["db_name"]

    if not _db_exists(db_name):
        return {"exists": False, "record_count": 0, "headers": []}

    if not is_configured():
        # DB files present but can't inspect without blast_bin
        return {"exists": True, "record_count": None, "headers": []}

    try:
        records = fetch_all_blast_records(
            db_name=db_name,
            blast_bin=settings["blast_bin"],
            workdir=settings["workdir"],
        )
        return {
            "exists": True,
            "record_count": len(records),
            "headers": [r.header for r in records],
        }
    except ValueError:
        return {"exists": True, "record_count": None, "headers": []}


@router.get("/status", response_model=DbStatusResponse)
def get_db_status():
    """Return whether the BLAST database exists and how many sequences it contains."""
    return _db_status_dict()


@router.post("/build", response_model=DbBuildResponse)
def build_database(body: DbBuildRequest):
    """
    Build (or overwrite) the BLAST reference database from FASTA text.
    Replaces any existing database entirely.
    """
    if not is_configured():
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    settings = get_settings()

    try:
        result = build_blast_database_from_fasta_text(
            fasta_text=body.fasta_text,
            db_name=settings["db_name"],
            blast_bin=settings["blast_bin"],
            workdir=settings["workdir"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if result.returncode != 0:
        detail = result.stderr.strip() or "makeblastdb failed with no error message."
        raise HTTPException(status_code=500, detail=f"BLAST DB build failed: {detail}")

    return DbBuildResponse(
        success=True,
        message="Database built successfully.",
        status=DbStatusResponse(**_db_status_dict()),
    )


@router.post("/add", response_model=DbBuildResponse)
def add_to_database(body: DbBuildRequest):
    """
    Merge new FASTA sequences into the existing BLAST database.
    If no database exists yet, behaves the same as /build.
    """
    if not is_configured():
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    settings = get_settings()
    db_name: str = settings["db_name"]
    blast_bin: str = settings["blast_bin"]
    workdir = Path(settings["workdir"])
    workdir.mkdir(parents=True, exist_ok=True)

    # Validate incoming FASTA before touching the filesystem
    try:
        parse_fasta_text(body.fasta_text)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if not _db_exists(db_name):
        # No existing DB — build fresh
        try:
            result = build_blast_database_from_fasta_text(
                fasta_text=body.fasta_text,
                db_name=db_name,
                blast_bin=blast_bin,
                workdir=workdir,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        if result.returncode != 0:
            detail = result.stderr.strip() or "makeblastdb failed."
            raise HTTPException(status_code=500, detail=f"BLAST DB build failed: {detail}")
    else:
        # DB exists — write temp FASTA file and merge into existing DB
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".fasta",
            prefix="blast_add_",
            dir=workdir,
            delete=False,
            encoding="utf-8",
        ) as tmp:
            tmp.write(body.fasta_text)
            tmp_path = Path(tmp.name)

        try:
            merge = add_fasta_to_blast_database(
                new_fasta=tmp_path,
                db_name=db_name,
                blast_bin=blast_bin,
                workdir=workdir,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        finally:
            tmp_path.unlink(missing_ok=True)

        build = merge.get("build_result")
        if build and build.returncode != 0:
            detail = (build.stderr or "").strip() or "makeblastdb failed."
            raise HTTPException(status_code=500, detail=f"BLAST DB merge failed: {detail}")

    return DbBuildResponse(
        success=True,
        message="Sequences added to database successfully.",
        status=DbStatusResponse(**_db_status_dict()),
    )


@router.delete("/clear", response_model=DbClearResponse)
def clear_database():
    """
    Delete all BLAST database files for the configured db_name prefix.
    The database can be rebuilt afterwards via /build.
    """
    settings = get_settings()
    db_path = Path(settings["db_name"])

    # Remove every file whose stem matches the database prefix (e.g. gene_db.nhr, .ndb, …)
    removed = 0
    for f in db_path.parent.glob(f"{db_path.name}.*"):
        try:
            f.unlink()
            removed += 1
        except OSError:
            pass  # skip locked/missing files

    if removed == 0:
        return DbClearResponse(
            success=True,
            message="No database files found — nothing to clear.",
            files_removed=0,
        )

    return DbClearResponse(
        success=True,
        message=f"Database cleared ({removed} file{'s' if removed != 1 else ''} removed).",
        files_removed=removed,
    )
