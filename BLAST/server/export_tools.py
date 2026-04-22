from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Iterable, Mapping


def write_text_export(text: str, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(text, encoding="utf-8")
    return path


def write_json_export(data: object, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def write_csv_export(
    rows: Iterable[Mapping[str, object]],
    output_path: str | Path,
    fieldnames: list[str] | None = None,
) -> Path:
    path = Path(output_path)
    row_list = [dict(row) for row in rows]

    if fieldnames is None:
        fieldnames = list(row_list[0].keys()) if row_list else []

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
        for row in row_list:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
    return path


def write_fasta_report_export(report_text: str, output_path: str | Path) -> Path:
    """Write a pre-formatted SNP analysis FASTA report to a file."""
    return write_text_export(report_text, output_path)
