from __future__ import annotations

from pathlib import Path
import tempfile
from typing import Dict, List

from Blast_code import FastaRecord, fasta_to_text, merge_into_existing_fasta, normalize_sequence, read_fasta, write_fasta


DEFAULT_DISEASE_FASTA = Path(__file__).parent / "disease_database" / "disease_snps.fa"


def preview_disease_database(disease_fasta: str | Path = DEFAULT_DISEASE_FASTA) -> str:
    return fasta_to_text(disease_fasta)


def summarize_disease_database(disease_fasta: str | Path = DEFAULT_DISEASE_FASTA) -> List[Dict[str, str]]:
    summary: List[Dict[str, str]] = []
    for record in read_fasta(disease_fasta):
        summary.append(
            {
                "header": record.header,
                "length": str(len(record.sequence)),
            }
        )
    return summary


def merge_snp_fasta_into_database(
    new_fasta_files: List[str | Path],
    disease_fasta: str | Path = DEFAULT_DISEASE_FASTA,
) -> Dict[str, object]:
    before = preview_disease_database(disease_fasta)
    merge_result = merge_into_existing_fasta(disease_fasta, new_fasta_files)
    after = preview_disease_database(disease_fasta)

    return {
        "before": before,
        "after": after,
        "merge_result": merge_result,
        "disease_fasta": str(disease_fasta),
    }


def add_snp_record_to_database(
    header: str,
    sequence: str,
    disease_fasta: str | Path = DEFAULT_DISEASE_FASTA,
) -> Dict[str, object]:
    existing_records = read_fasta(disease_fasta)
    new_record = FastaRecord(header=header.strip(), sequence=normalize_sequence(sequence))
    before = preview_disease_database(disease_fasta)

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".fasta",
        prefix="disease_record_",
        dir=str(Path(disease_fasta).parent),
        delete=False,
        encoding="utf-8",
    ) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        write_fasta([new_record], temp_path)
        merge_result = merge_into_existing_fasta(disease_fasta, [temp_path])
    finally:
        temp_path.unlink(missing_ok=True)

    after = preview_disease_database(disease_fasta)
    return {
        "before": before,
        "after": after,
        "merge_result": merge_result,
        "disease_fasta": str(disease_fasta),
        "record_header": header.strip(),
        "previous_count": len(existing_records),
    }
