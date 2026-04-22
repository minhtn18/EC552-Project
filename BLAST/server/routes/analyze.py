from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..paths import BLAST_ROOT  # also ensures BLAST_ROOT is on sys.path
from Blast_code import (
    normalize_sequence,
    parse_blast_tabular,
    run_blastn,
    write_single_fasta,
)
from disease_database_tools import DEFAULT_DISEASE_FASTA
from snp_analysis import analyze_with_disease_fasta, format_analysis_report

from ..config import NOT_CONFIGURED_DETAIL, get_settings, is_configured
from ..export_tools import write_csv_export, write_fasta_report_export, write_json_export, write_text_export
from ..models import AnalyzeRequest, AnalyzeResponse, ExportRequest, SNPResult

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
            return AnalyzeResponse(snps=[], fasta_report="")

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
    fasta_report = format_analysis_report(analysis, "analysis")
    return AnalyzeResponse(
        snps=[_map_report_row_to_snp(row, i + 1) for i, row in enumerate(report_rows)],
        fasta_report=fasta_report,
    )


# ── Export ────────────────────────────────────────────────────────────────────

_CSV_FIELDS = [
    "snpNo", "position", "refNucleotide", "varNucleotide",
    "codon", "aminoAcidChange", "gene", "disease", "pathogenicity",
]

_EXPORT_FORMATS = {"txt", "json", "csv", "fasta"}


def _snps_to_text(snps: List[SNPResult]) -> str:
    lines = [
        "CLEAVE SNP Analysis Report",
        "==========================",
        f"Total variants detected: {len(snps)}",
        "",
    ]
    for snp in snps:
        lines += [
            f"SNP #{snp.snpNo}",
            f"  Position      : {snp.position}",
            f"  Ref / Variant : {snp.refNucleotide} \u2192 {snp.varNucleotide}",
            f"  Codon         : {snp.codon}",
            f"  AA Change     : {snp.aminoAcidChange}",
            f"  Gene          : {snp.gene}",
            f"  Disease       : {snp.disease}",
            f"  Pathogenicity : {snp.pathogenicity}",
            "",
        ]
    return "\n".join(lines)


@router.post("/analyze/export")
def export_snps(body: ExportRequest):
    """
    Format SNP results as TXT, JSON, or CSV and return as a file download.
    The SNP list is supplied by the caller (already held in the frontend).
    """
    fmt = body.format.lower()
    if fmt not in _EXPORT_FORMATS:
        raise HTTPException(status_code=400, detail=f"Unsupported format '{fmt}'. Use: txt, json, csv.")

    snps = body.snps

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        if fmt == "json":
            out = tmp_path / "snp_results.json"
            write_json_export([s.model_dump() for s in snps], out)
            return Response(
                content=out.read_text(encoding="utf-8"),
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=snp_results.json"},
            )

        if fmt == "csv":
            out = tmp_path / "snp_results.csv"
            write_csv_export([s.model_dump() for s in snps], out, fieldnames=_CSV_FIELDS)
            return Response(
                content=out.read_text(encoding="utf-8"),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=snp_results.csv"},
            )

        if fmt == "fasta":
            if not body.fasta_report:
                raise HTTPException(status_code=400, detail="fasta_report is required when format='fasta'.")
            out = tmp_path / "snp_results.txt"
            write_fasta_report_export(body.fasta_report, out)
            return Response(
                content=out.read_text(encoding="utf-8"),
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=snp_results.txt"},
            )

        # txt (default)
        out = tmp_path / "snp_results.txt"
        write_text_export(_snps_to_text(snps), out)
        return Response(
            content=out.read_text(encoding="utf-8"),
            media_type="text/plain",
            headers={"Content-Disposition": "attachment; filename=snp_results.txt"},
        )
