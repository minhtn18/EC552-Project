from __future__ import annotations

from pathlib import Path
import json
from typing import Dict, List

from Blast_code import DEFAULT_DATABASE_NAME, FastaRecord, fetch_all_blast_records, normalize_sequence, parse_blast_tabular, read_fasta
from disease_database_tools import DEFAULT_DISEASE_FASTA


def parse_header_metadata(header: str) -> Dict[str, str]:
    metadata: Dict[str, str] = {}
    parts = [part.strip() for part in header.split("|") if part.strip()]
    if parts:
        metadata["label"] = parts[0]

    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        metadata[key.strip().lower()] = value.strip()
    return metadata


def load_known_variants_from_fasta(disease_fasta: str | Path) -> List[Dict[str, str | int]]:
    variants: List[Dict[str, str | int]] = []

    for record in read_fasta(disease_fasta):
        metadata = parse_header_metadata(record.header)
        reference_position = metadata.get("ref_pos") or metadata.get("reference_position")
        if not reference_position:
            continue

        variants.append(
            {
                "label": metadata.get("label", record.header),
                "gene": metadata.get("gene", ""),
                "variant_name": metadata.get("variant", ""),
                "pathogenicity": metadata.get("pathogenicity", "Unknown"),
                "harm_level": metadata.get("harm", metadata.get("harm_level", "Unknown")),
                "disease": metadata.get("disease", metadata.get("label", "")),
                "reference_position": int(reference_position),
                "reference_base": metadata.get("ref", ""),
                "patient_base": metadata.get("alt", ""),
                "sequence": record.sequence,
            }
        )

    return variants


def choose_best_hit(rows: List[Dict[str, str]]) -> Dict[str, str]:
    if not rows:
        raise ValueError("No BLAST rows were provided.")

    def sort_key(row: Dict[str, str]) -> tuple[float, float]:
        return (float(row["bitscore"]), float(row["pident"]))

    snp_safe_rows = [
        row
        for row in rows
        if int(row.get("mismatch", "0")) > 0
        and int(row.get("gapopen", "0")) == 0
        and (abs(int(row["qend"]) - int(row["qstart"])) + 1) == (abs(int(row["send"]) - int(row["sstart"])) + 1)
    ]
    if snp_safe_rows:
        return max(snp_safe_rows, key=sort_key)

    mismatch_rows = [row for row in rows if int(row.get("mismatch", "0")) > 0]
    if mismatch_rows:
        return max(mismatch_rows, key=sort_key)
    return max(rows, key=sort_key)


def get_sequence_from_database(
    db_name: str | Path,
    header: str,
    blast_bin: str | Path,
    workdir: str | Path | None = None,
) -> FastaRecord:
    records = fetch_all_blast_records(db_name=db_name, blast_bin=blast_bin, workdir=workdir)
    for record in records:
        record_id = record.header.split()[0]
        if record.header == header or record_id == header:
            return record
    raise ValueError(f"Reference header not found in BLAST database: {header}")


def get_query_record(query_source: str | Path, query_header: str | None = None) -> FastaRecord:
    path = Path(query_source)
    if path.exists():
        records = read_fasta(path)
        if not records:
            raise ValueError("Query FASTA contains no records.")
        if query_header:
            for record in records:
                if record.header == query_header:
                    return record
            raise ValueError(f"Query header not found in FASTA: {query_header}")
        return records[0]

    if not query_header:
        query_header = "user_query"
    return FastaRecord(header=query_header, sequence=normalize_sequence(str(query_source)))


def slice_alignment_region(sequence: str, start: str, end: str) -> str:
    start_index = int(start) - 1
    end_index = int(end)
    return normalize_sequence(sequence)[start_index:end_index]


def get_sequence_context(sequence: str, position: int, flank: int = 20) -> Dict[str, str]:
    normalized = normalize_sequence(sequence)
    zero_based = position - 1
    start = max(0, zero_based - flank)
    end = min(len(normalized), zero_based + flank + 1)
    return {"window": normalized[start:end]}


def get_atg_relative_position(sequence: str, position: int) -> int | None:
    normalized = normalize_sequence(sequence)
    zero_based = position - 1
    nearest_start = None

    for index in range(max(0, zero_based - 300), zero_based + 1):
        if normalized[index:index + 3] == "ATG":
            nearest_start = index + 1

    if nearest_start is None:
        return None
    return position - nearest_start + 1


def enrich_snp_coordinates(
    snps: List[Dict[str, str | int]],
    best_hit: Dict[str, str],
    query_sequence: str,
    reference_sequence: str,
) -> List[Dict[str, str | int]]:
    enriched: List[Dict[str, str | int]] = []
    reference_forward = int(best_hit["sstart"]) <= int(best_hit["send"])

    for snp in snps:
        query_position = int(snp["query_position"])
        reference_position = int(snp["reference_position"])
        enriched_snp = dict(snp)
        enriched_snp["query_aligned_position"] = query_position - int(best_hit["qstart"]) + 1
        enriched_snp["reference_aligned_position"] = (
            reference_position - int(best_hit["sstart"]) + 1
            if reference_forward
            else int(best_hit["sstart"]) - reference_position + 1
        )
        enriched_snp["query_atg_relative_position"] = get_atg_relative_position(query_sequence, query_position)
        enriched_snp["reference_atg_relative_position"] = get_atg_relative_position(reference_sequence, reference_position)
        enriched.append(enriched_snp)

    return enriched


def compare_aligned_sequences(
    query_sequence: str,
    reference_sequence: str,
    query_start: str,
    query_end: str,
    reference_start: str,
    reference_end: str,
) -> List[Dict[str, str | int]]:
    query_region = slice_alignment_region(query_sequence, query_start, query_end)
    reference_region = slice_alignment_region(reference_sequence, reference_start, reference_end)

    if len(query_region) != len(reference_region):
        raise ValueError(
            "Aligned query and reference regions are different lengths. "
            f"Query region length: {len(query_region)}, reference region length: {len(reference_region)}. "
            "This usually means the selected BLAST hit contains a gap/indel or the query input used for SNP analysis "
            "is not the same sequence used for the BLAST run."
        )

    snps: List[Dict[str, str | int]] = []
    reference_forward = int(reference_start) <= int(reference_end)

    for index, (query_base, reference_base) in enumerate(zip(query_region, reference_region), start=0):
        if query_base == reference_base:
            continue

        query_position = int(query_start) + index
        if reference_forward:
            reference_position = int(reference_start) + index
        else:
            reference_position = int(reference_start) - index

        snps.append(
            {
                "query_position": query_position,
                "reference_position": reference_position,
                "reference_base": reference_base,
                "patient_base": query_base,
                "change": f"{reference_base}>{query_base}",
            }
        )

    return snps


def match_known_variants(
    snps: List[Dict[str, str | int]],
    known_variants: List[Dict[str, str | int]],
    query_sequence: str | None = None,
) -> List[Dict[str, str | int]]:
    matches: List[Dict[str, str | int]] = []
    normalized_query = normalize_sequence(query_sequence) if query_sequence else None

    for snp in snps:
        for variant in known_variants:
            same_change = (
                snp["reference_base"] == variant.get("reference_base")
                and snp["patient_base"] == variant.get("patient_base")
            )
            position_match = (
                snp["reference_position"] == variant.get("reference_position")
                or snp["query_position"] == variant.get("reference_position")
                or snp.get("query_aligned_position") == variant.get("reference_position")
                or snp.get("reference_aligned_position") == variant.get("reference_position")
                or snp.get("query_atg_relative_position") == variant.get("reference_position")
                or snp.get("reference_atg_relative_position") == variant.get("reference_position")
            )
            sequence_match = False
            variant_sequence = variant.get("sequence")
            if normalized_query and isinstance(variant_sequence, str):
                normalized_variant_sequence = normalize_sequence(variant_sequence)
                sequence_match = (
                    normalized_variant_sequence in normalized_query
                    or normalized_query in normalized_variant_sequence
                )
            if same_change and (position_match or sequence_match):
                merged = dict(snp)
                merged.update(variant)
                matches.append(merged)

    return matches


def analyze_best_blast_hit(
    blast_rows: List[Dict[str, str]],
    db_name: str | Path,
    blast_bin: str | Path,
    query_source: str | Path,
    query_header: str | None = None,
    known_variants: List[Dict[str, str | int]] | None = None,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    best_hit = choose_best_hit(blast_rows)
    query_span = abs(int(best_hit["qend"]) - int(best_hit["qstart"])) + 1
    reference_span = abs(int(best_hit["send"]) - int(best_hit["sstart"])) + 1
    if int(best_hit.get("gapopen", "0")) > 0 or query_span != reference_span:
        raise ValueError(
            "The selected BLAST hit is not SNP-only. "
            f"gapopen={best_hit.get('gapopen', '0')}, query span={query_span}, reference span={reference_span}. "
            "Current SNP analysis supports substitution-style mismatches, not indels. "
            "Use a hit with gapopen=0, or update the query/reference input."
        )
    reference_record = get_sequence_from_database(db_name, best_hit["sseqid"], blast_bin, workdir=workdir)
    query_record = get_query_record(query_source, query_header=query_header)

    snps = compare_aligned_sequences(
        query_sequence=query_record.sequence,
        reference_sequence=reference_record.sequence,
        query_start=best_hit["qstart"],
        query_end=best_hit["qend"],
        reference_start=best_hit["sstart"],
        reference_end=best_hit["send"],
    )
    snps = enrich_snp_coordinates(
        snps=snps,
        best_hit=best_hit,
        query_sequence=query_record.sequence,
        reference_sequence=reference_record.sequence,
    )

    variant_matches: List[Dict[str, str | int]] = []
    if known_variants:
        variant_matches = match_known_variants(snps, known_variants, query_sequence=query_record.sequence)

    return {
        "best_hit": best_hit,
        "reference_header": reference_record.header,
        "query_header": query_record.header,
        "snp_count": len(snps),
        "snps": snps,
        "known_variant_matches": variant_matches,
    }


def analyze_with_disease_fasta(
    blast_rows: List[Dict[str, str]],
    db_name: str | Path,
    blast_bin: str | Path,
    query_source: str | Path,
    disease_fasta: str | Path,
    query_header: str | None = None,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    known_variants = load_known_variants_from_fasta(disease_fasta)
    best_hit = choose_best_hit(blast_rows)
    reference_record = get_sequence_from_database(db_name, best_hit["sseqid"], blast_bin, workdir=workdir)
    query_record = get_query_record(query_source, query_header=query_header)
    result = analyze_best_blast_hit(
        blast_rows=blast_rows,
        db_name=db_name,
        blast_bin=blast_bin,
        query_source=query_source,
        query_header=query_header,
        known_variants=known_variants,
        workdir=workdir,
    )

    snps = result["snps"]
    matches = result["known_variant_matches"]

    if not snps:
        result["message"] = "No identified known SNP disease in the matched region."
        result["report_rows"] = []
        return result

    report_rows: List[Dict[str, str | int]] = []
    for index, snp in enumerate(snps, start=1):
        matched_variant = next(
            (
                variant
                for variant in matches
                if (
                    variant["reference_base"] == snp["reference_base"]
                    and variant["patient_base"] == snp["patient_base"]
                    and (
                        variant["reference_position"] == snp["reference_position"]
                        or variant["reference_position"] == snp["query_position"]
                        or variant["reference_position"] == (int(snp["query_position"]) - int(best_hit["qstart"]) + 1)
                        or variant["reference_position"]
                        == (
                            int(snp["reference_position"]) - int(best_hit["sstart"]) + 1
                            if int(best_hit["sstart"]) <= int(best_hit["send"])
                            else int(best_hit["sstart"]) - int(snp["reference_position"]) + 1
                        )
                        or variant["reference_position"] == get_atg_relative_position(query_record.sequence, int(snp["query_position"]))
                        or variant["reference_position"] == get_atg_relative_position(reference_record.sequence, int(snp["reference_position"]))
                    )
                )
            ),
            None,
        )
        query_context = get_sequence_context(query_record.sequence, int(snp["query_position"]))
        reference_context = get_sequence_context(reference_record.sequence, int(snp["reference_position"]))
        query_atg_relative_position = snp.get("query_atg_relative_position")
        reference_atg_relative_position = snp.get("reference_atg_relative_position")

        report_rows.append(
            {
                "index": index,
                "sseqid": best_hit["sseqid"],
                "query_position": snp["query_position"],
                "query_global_position": snp["query_position"],
                "query_aligned_position": snp.get("query_aligned_position"),
                "query_atg_relative_position": query_atg_relative_position,
                "reference_position": snp["reference_position"],
                "reference_global_position": snp["reference_position"],
                "reference_aligned_position": snp.get("reference_aligned_position"),
                "reference_atg_relative_position": reference_atg_relative_position,
                "query_base": snp["patient_base"],
                "supposed_base": snp["reference_base"],
                "change": snp["change"],
                "query_context": query_context["window"],
                "reference_context": reference_context["window"],
                "pathogenicity": matched_variant.get("pathogenicity", "Unknown") if matched_variant else "Unknown",
                "harm_level": matched_variant.get("harm_level", "Unknown") if matched_variant else "Unknown",
                "disease": matched_variant.get("disease", "Unknown") if matched_variant else "Unknown",
                "variant_name": matched_variant.get("variant_name", "Unknown") if matched_variant else "Unknown",
                "qstart": int(best_hit["qstart"]),
                "qend": int(best_hit["qend"]),
            }
        )

    result["message"] = "Known SNP disease match found." if matches else "Variant detected but no known SNP disease match found."
    result["report_rows"] = report_rows
    return result


def analyze_results_file(
    results_file: str | Path,
    blast_bin: str | Path,
    query_source: str | Path,
    db_name: str | Path | None = None,
    disease_fasta: str | Path = DEFAULT_DISEASE_FASTA,
    query_header: str | None = None,
    workdir: str | Path | None = None,
) -> Dict[str, object]:
    blast_rows = parse_blast_tabular(results_file)
    if not blast_rows:
        raise ValueError(f"No BLAST rows found in results file: {results_file}")
    return analyze_with_disease_fasta(
        blast_rows=blast_rows,
        db_name=db_name or DEFAULT_DATABASE_NAME,
        blast_bin=blast_bin,
        query_source=query_source,
        disease_fasta=disease_fasta,
        query_header=query_header,
        workdir=workdir,
    )


def format_analysis_report(result: Dict[str, object], results_file: str | Path) -> str:
    lines = [
        f"SNP analysis from {results_file}",
        f"Query: {result['query_header']}",
        f"Best match: {result['reference_header']}",
        f"Summary: {result['message']}",
        f"Detected SNP count: {result['snp_count']}",
        "",
    ]

    report_rows = result.get("report_rows", [])
    if not report_rows:
        lines.append("No SNP report rows were generated.")
        return "\n".join(lines)

    for row in report_rows:
        lines.append(
            f"SNP {row['index']}: query pos {row['query_global_position']}, ref pos {row['reference_global_position']}, "
            f"base {row['supposed_base']}->{row['query_base']}, disease={row['disease']}, "
            f"variant={row['variant_name']}, pathogenicity={row['pathogenicity']}, harm={row['harm_level']}"
        )
        lines.append(f"Query context: {row['query_context']}")
        lines.append(f"Reference context: {row['reference_context']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run SNP analysis directly from a BLAST results file and database.")
    parser.add_argument("--results", required=True, help="BLAST results file in outfmt 6 tabular format.")
    parser.add_argument("--blast-bin", required=True, help="Folder containing blastdbcmd.exe.")
    parser.add_argument("--query", required=True, help="Query FASTA path or raw query DNA sequence.")
    parser.add_argument("--db", default=DEFAULT_DATABASE_NAME, help=f"BLAST database name or prefix. Default: {DEFAULT_DATABASE_NAME}")
    parser.add_argument("--query-header", default=None, help="Query FASTA header to use when needed.")
    parser.add_argument("--disease-fasta", default=str(DEFAULT_DISEASE_FASTA), help="Disease SNP FASTA metadata file.")
    parser.add_argument("--json", action="store_true", help="Print raw JSON instead of a text report.")
    args = parser.parse_args()

    analysis = analyze_results_file(
        results_file=args.results,
        blast_bin=args.blast_bin,
        query_source=args.query,
        db_name=args.db,
        disease_fasta=args.disease_fasta,
        query_header=args.query_header,
    )
    if args.json:
        print(json.dumps(analysis, indent=2))
    else:
        print(format_analysis_report(analysis, args.results))
