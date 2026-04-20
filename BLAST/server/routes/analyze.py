from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from ..paths import BLAST_ROOT  # also ensures BLAST_ROOT is on sys.path
from Blast_code import (
    normalize_sequence,
    parse_blast_tabular,
    run_blastn,
    write_single_fasta,
)
from disease_database_tools import DEFAULT_DISEASE_FASTA
from snp_analysis import analyze_with_disease_fasta

from ..config import NOT_CONFIGURED_DETAIL, get_settings, is_configured
from ..models import AnalyzeRequest, AnalyzeResponse, SNPResult

router = APIRouter(tags=["analyze"])


def _map_report_row_to_snp(row: dict, index: int) -> SNPResult:
    disease_raw = str(row.get("disease", "Unknown"))
    disease = disease_raw.replace("_", " ") if disease_raw != "Unknown" else "Unknown"
    return SNPResult(
        snpNo=index,
        position=int(row.get("query_position", row.get("query_global_position", 0))),
        refNucleotide=str(row.get("supposed_base", "")),
        varNucleotide=str(row.get("query_base", "")),
        codon="—",
        aminoAcidChange="—",
        gene=str(row.get("gene", "HBB")),
        disease=disease,
        pathogenicity=str(row.get("pathogenicity", "Unknown")),
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_sequence(body: AnalyzeRequest):
    """
    Align the submitted sequence against the BLAST reference database and
    return any SNPs that match known disease variants in the disease FASTA.
    Codon and amino-acid fields are placeholders pending translation logic.
    """
    if not is_configured():
        raise HTTPException(status_code=503, detail=NOT_CONFIGURED_DETAIL)

    settings = get_settings()
    blast_bin: str = settings["blast_bin"]
    db_name: str = settings["db_name"]
    workdir = Path(settings["workdir"])
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        sequence = normalize_sequence(body.sequence)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    with tempfile.TemporaryDirectory(dir=workdir) as tmp:
        tmp_path = Path(tmp)
        query_fasta = tmp_path / "query.fasta"
        results_file = tmp_path / "results.txt"

        write_single_fasta("user_query", sequence, query_fasta)

        blast_result = run_blastn(
            query_fasta=query_fasta,
            db_name=db_name,
            output_file=results_file,
            blast_bin=blast_bin,
        )

        if blast_result.returncode != 0:
            detail = blast_result.stderr.strip() or "blastn failed with no error message."
            raise HTTPException(status_code=500, detail=f"BLAST error: {detail}")

        blast_rows = parse_blast_tabular(results_file)
        if not blast_rows:
            return AnalyzeResponse(snps=[])

        try:
            analysis = analyze_with_disease_fasta(
                blast_rows=blast_rows,
                db_name=db_name,
                blast_bin=blast_bin,
                query_source=query_fasta,
                disease_fasta=DEFAULT_DISEASE_FASTA,
                workdir=workdir,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))

    report_rows: List[dict] = analysis.get("report_rows", [])
    return AnalyzeResponse(
        snps=[_map_report_row_to_snp(row, i + 1) for i, row in enumerate(report_rows)]
    )
