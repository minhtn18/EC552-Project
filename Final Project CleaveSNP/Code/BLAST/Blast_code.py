from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Dict, List


VALID_DNA = set("ACGTN")
DEFAULT_DATABASE_NAME = "gene_db"


@dataclass
class FastaRecord:
    header: str
    sequence: str


def normalize_sequence(sequence: str) -> str:
    cleaned = "".join(sequence.split()).upper()
    if not cleaned:
        raise ValueError("Sequence is empty.")
    invalid = sorted(set(cleaned) - VALID_DNA)
    if invalid:
        raise ValueError(f"Sequence contains invalid DNA characters: {', '.join(invalid)}")
    return cleaned


def read_fasta(fasta_path: str | Path) -> List[FastaRecord]:
    path = Path(fasta_path)
    if not path.exists():
        return []

    records: List[FastaRecord] = []
    header: str | None = None
    sequence_lines: List[str] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append(FastaRecord(header=header, sequence=normalize_sequence("".join(sequence_lines))))
            header = line[1:].strip()
            if not header:
                raise ValueError(f"FASTA header is empty in {path}")
            sequence_lines = []
        else:
            if header is None:
                raise ValueError(f"Sequence found before FASTA header in {path}")
            sequence_lines.append(line)

    if header is not None:
        records.append(FastaRecord(header=header, sequence=normalize_sequence("".join(sequence_lines))))

    return records


def write_fasta(records: List[FastaRecord], fasta_path: str | Path, line_width: int = 80) -> None:
    path = Path(fasta_path)
    lines: List[str] = []
    for record in records:
        lines.append(f">{record.header}")
        sequence = normalize_sequence(record.sequence)
        lines.extend(sequence[i:i + line_width] for i in range(0, len(sequence), line_width))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def fasta_to_text(fasta_path: str | Path) -> str:
    path = Path(fasta_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_single_fasta(header: str, sequence: str, fasta_path: str | Path, line_width: int = 80) -> None:
    if not header.strip():
        raise ValueError("Header cannot be empty.")
    write_fasta([FastaRecord(header=header.strip(), sequence=sequence)], fasta_path, line_width=line_width)


def write_fasta_from_text(fasta_text: str, fasta_path: str | Path) -> None:
    text = fasta_text.strip()
    if not text:
        raise ValueError("FASTA text is empty.")
    records = parse_fasta_text(text)
    write_fasta(records, fasta_path)


def parse_fasta_text(fasta_text: str) -> List[FastaRecord]:
    text = fasta_text.strip()
    if not text:
        raise ValueError("FASTA text is empty.")

    records: List[FastaRecord] = []
    header: str | None = None
    sequence_lines: List[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append(FastaRecord(header=header, sequence=normalize_sequence("".join(sequence_lines))))
            header = line[1:].strip()
            if not header:
                raise ValueError("FASTA header cannot be empty.")
            sequence_lines = []
        else:
            if header is None:
                raise ValueError("FASTA text must start with a header line beginning with '>'.")
            sequence_lines.append(line)

    if header is not None:
        records.append(FastaRecord(header=header, sequence=normalize_sequence("".join(sequence_lines))))

    if not records:
        raise ValueError("No FASTA records found.")
    return records


def find_duplicate(new_record: FastaRecord, existing_records: List[FastaRecord]) -> Dict[str, str] | None:
    normalized_header = new_record.header.strip()
    normalized_sequence = normalize_sequence(new_record.sequence)

    for record in existing_records:
        if record.header.strip() == normalized_header:
            return {"type": "header", "match": record.header}
        if normalize_sequence(record.sequence) == normalized_sequence:
            return {"type": "sequence", "match": record.header}
    return None


def add_sequence_to_fasta(
    fasta_path: str | Path,
    header: str,
    sequence: str,
    allow_duplicate_headers: bool = False,
    allow_duplicate_sequences: bool = False,
) -> Dict[str, str]:
    if not header.strip():
        raise ValueError("Header cannot be empty.")

    new_record = FastaRecord(header=header.strip(), sequence=normalize_sequence(sequence))
    existing_records = read_fasta(fasta_path)
    duplicate = find_duplicate(new_record, existing_records)

    if duplicate:
        if duplicate["type"] == "header" and not allow_duplicate_headers:
            return {"status": "skipped", "reason": f"Duplicate header: {duplicate['match']}"}
        if duplicate["type"] == "sequence" and not allow_duplicate_sequences:
            return {"status": "skipped", "reason": f"Duplicate sequence already stored as: {duplicate['match']}"}

    existing_records.append(new_record)
    write_fasta(existing_records, fasta_path)
    return {"status": "added", "reason": f"Added sequence: {new_record.header}"}


def deduplicate_records(records: List[FastaRecord]) -> tuple[List[FastaRecord], List[Dict[str, str]]]:
    unique_records: List[FastaRecord] = []
    seen_sequences: Dict[str, str] = {}
    duplicates: List[Dict[str, str]] = []

    for record in records:
        normalized_sequence = normalize_sequence(record.sequence)
        if normalized_sequence in seen_sequences:
            duplicates.append(
                {
                    "removed_header": record.header,
                    "kept_header": seen_sequences[normalized_sequence],
                }
            )
            continue
        seen_sequences[normalized_sequence] = record.header
        unique_records.append(FastaRecord(header=record.header, sequence=normalized_sequence))

    return unique_records, duplicates


def merge_fasta_records(record_groups: List[List[FastaRecord]]) -> Dict[str, object]:
    combined: List[FastaRecord] = []
    for group in record_groups:
        combined.extend(group)

    unique_records, duplicates = deduplicate_records(combined)
    return {
        "records": unique_records,
        "duplicates_removed": duplicates,
        "input_count": len(combined),
        "output_count": len(unique_records),
    }


def merge_fasta_files(
    source_files: List[str | Path],
    output_fasta: str | Path,
) -> Dict[str, object]:
    record_groups = [read_fasta(source_file) for source_file in source_files]
    merge_result = merge_fasta_records(record_groups)
    write_fasta(merge_result["records"], output_fasta)
    return merge_result


def merge_into_existing_fasta(
    existing_fasta: str | Path,
    new_sources: List[str | Path],
) -> Dict[str, object]:
    existing_records = read_fasta(existing_fasta)
    new_record_groups = [read_fasta(source_file) for source_file in new_sources]
    merge_result = merge_fasta_records([existing_records, *new_record_groups])
    write_fasta(merge_result["records"], existing_fasta)
    return merge_result


def run_command(command: List[str], workdir: str | Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(workdir) if workdir else None,
        capture_output=True,
        text=True,
        check=False,
    )


def resolve_database_prefix(db_name: str | Path | None, blast_bin: str | Path) -> Path:
    db_value = db_name if db_name else DEFAULT_DATABASE_NAME
    db_path = Path(db_value)
    if db_path.is_absolute():
        return db_path

    blast_bin_path = Path(blast_bin)
    blast_bin_candidate = blast_bin_path / db_path
    local_candidate = Path.cwd() / db_path

    blast_db_exists = any((blast_bin_candidate.parent / f"{blast_bin_candidate.name}{suffix}").exists() for suffix in (".nhr", ".nin", ".nsq", ".ndb"))
    local_db_exists = any((local_candidate.parent / f"{local_candidate.name}{suffix}").exists() for suffix in (".nhr", ".nin", ".nsq", ".ndb"))

    if blast_db_exists:
        return blast_bin_candidate
    if local_db_exists:
        return local_candidate
    return blast_bin_candidate


def build_blast_database(
    reference_fasta: str | Path,
    db_name: str | Path | None,
    blast_bin: str | Path,
    dbtype: str = "nucl",
    workdir: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    blast_bin_path = Path(blast_bin)
    db_prefix = resolve_database_prefix(db_name, blast_bin_path)
    command = [
        str(blast_bin_path / "makeblastdb.exe"),
        "-in",
        str(reference_fasta),
        "-dbtype",
        dbtype,
        "-out",
        str(db_prefix),
    ]
    return run_command(command, workdir=workdir)


def build_blast_database_from_sequence(
    reference_sequence: str,
    reference_header: str,
    db_name: str,
    blast_bin: str | Path,
    dbtype: str = "nucl",
    workdir: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    temp_dir = Path(workdir) if workdir else Path.cwd()
    temp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        prefix="blast_reference_",
        dir=temp_dir,
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        write_single_fasta(reference_header, reference_sequence, temp_path)
        return build_blast_database(temp_path, db_name, blast_bin, dbtype=dbtype, workdir=workdir)
    finally:
        temp_path.unlink(missing_ok=True)


def build_blast_database_from_fasta_text(
    fasta_text: str,
    db_name: str,
    blast_bin: str | Path,
    dbtype: str = "nucl",
    workdir: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    temp_dir = Path(workdir) if workdir else Path.cwd()
    temp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        prefix="blast_reference_",
        dir=temp_dir,
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        write_fasta_from_text(fasta_text, temp_path)
        return build_blast_database(temp_path, db_name, blast_bin, dbtype=dbtype, workdir=workdir)
    finally:
        temp_path.unlink(missing_ok=True)


def run_blastn(
    query_fasta: str | Path,
    db_name: str | Path | None,
    output_file: str | Path,
    blast_bin: str | Path,
    outfmt: str = "6",
    workdir: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    blast_bin_path = Path(blast_bin)
    db_prefix = resolve_database_prefix(db_name, blast_bin_path)
    command = [
        str(blast_bin_path / "blastn.exe"),
        "-query",
        str(query_fasta),
        "-db",
        str(db_prefix),
        "-out",
        str(output_file),
        "-outfmt",
        outfmt,
    ]
    return run_command(command, workdir=workdir)


def fetch_blast_record(
    db_name: str | Path | None,
    entry_id: str,
    blast_bin: str | Path,
    workdir: str | Path | None = None,
) -> FastaRecord:
    blast_bin_path = Path(blast_bin)
    db_prefix = resolve_database_prefix(db_name, blast_bin_path)
    command = [
        str(blast_bin_path / "blastdbcmd.exe"),
        "-db",
        str(db_prefix),
        "-entry",
        entry_id,
    ]
    result = run_command(command, workdir=workdir)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"blastdbcmd failed for entry: {entry_id}"
        raise ValueError(message)

    records = parse_fasta_text(result.stdout)
    if not records:
        raise ValueError(f"No BLAST database record returned for entry: {entry_id}")
    return records[0]


def fetch_all_blast_records(
    db_name: str | Path | None,
    blast_bin: str | Path,
    workdir: str | Path | None = None,
) -> List[FastaRecord]:
    blast_bin_path = Path(blast_bin)
    db_prefix = resolve_database_prefix(db_name, blast_bin_path)
    command = [
        str(blast_bin_path / "blastdbcmd.exe"),
        "-db",
        str(db_prefix),
        "-entry",
        "all",
    ]
    result = run_command(command, workdir=workdir)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or f"blastdbcmd failed for database: {db_name}"
        raise ValueError(message)
    return parse_fasta_text(result.stdout)


def add_fasta_to_blast_database(
    new_fasta: str | Path,
    db_name: str | Path | None,
    blast_bin: str | Path,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    existing_records = fetch_all_blast_records(db_name=db_name, blast_bin=blast_bin, workdir=workdir)
    new_records = read_fasta(new_fasta)
    merge_result = merge_fasta_records([existing_records, new_records])

    temp_dir = Path(workdir) if workdir else Path.cwd()
    temp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        prefix="blast_merged_",
        dir=temp_dir,
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        write_fasta(merge_result["records"], temp_path)
        build_result = build_blast_database(temp_path, db_name, blast_bin, workdir=workdir)
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "merge_result": merge_result,
        "build_result": build_result,
        "database": str(db_name),
        "source_fasta": str(new_fasta),
    }


def add_sequence_to_blast_database(
    header: str,
    sequence: str,
    db_name: str | Path | None,
    blast_bin: str | Path,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    existing_records = fetch_all_blast_records(db_name=db_name, blast_bin=blast_bin, workdir=workdir)
    merge_result = merge_fasta_records(
        [
            existing_records,
            [FastaRecord(header=header.strip(), sequence=normalize_sequence(sequence))],
        ]
    )

    temp_dir = Path(workdir) if workdir else Path.cwd()
    temp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        prefix="blast_single_add_",
        dir=temp_dir,
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        write_fasta(merge_result["records"], temp_path)
        build_result = build_blast_database(temp_path, db_name, blast_bin, workdir=workdir)
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "merge_result": merge_result,
        "build_result": build_result,
        "database": str(db_name),
        "header": header.strip(),
    }


def run_blastn_from_sequence(
    query_sequence: str,
    db_name: str | Path | None,
    output_file: str | Path,
    blast_bin: str | Path,
    query_header: str = "user_query",
    outfmt: str = "6",
    workdir: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    normalized = normalize_sequence(query_sequence)
    temp_dir = Path(workdir) if workdir else Path.cwd()
    temp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        prefix="blast_query_",
        dir=temp_dir,
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        write_single_fasta(query_header, normalized, temp_path)
        return run_blastn(temp_path, db_name, output_file, blast_bin, outfmt=outfmt, workdir=workdir)
    finally:
        temp_path.unlink(missing_ok=True)


def parse_blast_tabular(results_file: str | Path) -> List[Dict[str, str]]:
    path = Path(results_file)
    if not path.exists():
        return []

    columns = [
        "qseqid",
        "sseqid",
        "pident",
        "length",
        "mismatch",
        "gapopen",
        "qstart",
        "qend",
        "sstart",
        "send",
        "evalue",
        "bitscore",
    ]

    rows: List[Dict[str, str]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        values = line.split("\t")
        rows.append(dict(zip(columns, values)))
    return rows

