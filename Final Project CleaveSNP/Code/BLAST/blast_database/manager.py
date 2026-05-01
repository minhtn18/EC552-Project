from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Dict, List

from Blast_code import (
    DEFAULT_DATABASE_NAME,
    FastaRecord,
    add_fasta_to_blast_database,
    add_sequence_to_blast_database,
    build_blast_database,
    fetch_all_blast_records,
    normalize_sequence,
    resolve_database_prefix,
    write_fasta,
)


def inspect_database(
    blast_bin: str | Path,
    db_name: str | Path | None = None,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    records = fetch_all_blast_records(db_name=db_name, blast_bin=blast_bin, workdir=workdir)
    db_prefix = resolve_database_prefix(db_name or DEFAULT_DATABASE_NAME, blast_bin)
    return {
        "database": str(db_prefix),
        "record_count": len(records),
        "headers": [record.header for record in records],
    }


def list_record_headers(
    blast_bin: str | Path,
    db_name: str | Path | None = None,
    workdir: str | Path | None = None,
) -> List[str]:
    result = inspect_database(blast_bin=blast_bin, db_name=db_name, workdir=workdir)
    return result["headers"]


def preview_database_fasta(
    blast_bin: str | Path,
    db_name: str | Path | None = None,
    workdir: str | Path | None = None,
) -> str:
    records = fetch_all_blast_records(db_name=db_name, blast_bin=blast_bin, workdir=workdir)
    lines: List[str] = []
    for record in records:
        lines.append(f">{record.header}")
        lines.append(record.sequence)
    return "\n".join(lines) + ("\n" if lines else "")


def add_fasta_file(
    fasta_path: str | Path,
    blast_bin: str | Path,
    db_name: str | Path | None = None,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    return add_fasta_to_blast_database(
        new_fasta=fasta_path,
        db_name=db_name or DEFAULT_DATABASE_NAME,
        blast_bin=blast_bin,
        workdir=workdir,
    )


def add_sequence_record(
    header: str,
    sequence: str,
    blast_bin: str | Path,
    db_name: str | Path | None = None,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    return add_sequence_to_blast_database(
        header=header,
        sequence=sequence,
        db_name=db_name or DEFAULT_DATABASE_NAME,
        blast_bin=blast_bin,
        workdir=workdir,
    )


def modify_record(
    entry_id: str,
    new_sequence: str,
    blast_bin: str | Path,
    db_name: str | Path | None = None,
    new_header: str | None = None,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    records = fetch_all_blast_records(db_name=db_name, blast_bin=blast_bin, workdir=workdir)
    updated_records: List[FastaRecord] = []
    found = False

    for record in records:
        record_id = record.header.split()[0]
        if record.header == entry_id or record_id == entry_id:
            found = True
            updated_records.append(
                FastaRecord(
                    header=(new_header.strip() if new_header else record.header),
                    sequence=normalize_sequence(new_sequence),
                )
            )
        else:
            updated_records.append(record)

    if not found:
        raise ValueError(f"Database record not found: {entry_id}")

    db_prefix = resolve_database_prefix(db_name or DEFAULT_DATABASE_NAME, blast_bin)
    temp_dir = Path(workdir) if workdir else Path.cwd()
    temp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        prefix="blast_db_modify_",
        dir=temp_dir,
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        write_fasta(updated_records, temp_path)
        build_result = build_blast_database(
            reference_fasta=temp_path,
            db_name=db_prefix,
            blast_bin=blast_bin,
            workdir=workdir,
        )
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "database": str(db_prefix),
        "updated_entry": entry_id,
        "build_result": build_result,
        "record_count": len(updated_records),
    }
