from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


# ── Config ────────────────────────────────────────────────────────────────────

class ConfigRequest(BaseModel):
    blast_bin: str
    # db_name and workdir are auto-computed server-side — not accepted from the user


class ConfigResponse(BaseModel):
    blast_bin: str
    db_name: str
    workdir: str
    configured: bool


# ── Analyze ───────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    sequence: str
    format: Optional[str] = "raw"


class SNPResult(BaseModel):
    snpNo: int
    position: int
    refNucleotide: str
    varNucleotide: str
    codon: str           # placeholder "—" until translation logic is added
    aminoAcidChange: str # placeholder "—" until translation logic is added
    gene: str
    disease: str
    pathogenicity: str


class AnalyzeResponse(BaseModel):
    snps: List[SNPResult]
    fasta_report: str = ""  # pre-formatted SNP report from format_analysis_report()


class ExportRequest(BaseModel):
    snps: List[SNPResult]
    format: str           # "txt" | "json" | "csv" | "fasta"
    fasta_report: str = ""  # pre-formatted report text; required when format="fasta"


# ── Sequences ─────────────────────────────────────────────────────────────────

class SequenceRecord(BaseModel):
    id: Optional[int] = None
    name: str
    gene: str
    organism: str
    length: Optional[int] = None
    description: Optional[str] = ""
    sequence: str
    added: Optional[str] = None


# ── Database management ───────────────────────────────────────────────────────

class DbStatusResponse(BaseModel):
    exists: bool
    record_count: Optional[int]  # None when blast_bin not configured
    headers: List[str]           # empty when DB absent or blast_bin missing


class DbBuildRequest(BaseModel):
    fasta_text: str


class DbBuildResponse(BaseModel):
    success: bool
    message: str
    status: DbStatusResponse


class DbClearResponse(BaseModel):
    success: bool
    message: str
    files_removed: int


# ── CRISPR Design ─────────────────────────────────────────────────────────────

class CrisprDesignRequest(BaseModel):
    snp: Dict[str, Any]
    surroundingSequence: str
    windowSize: Optional[int] = 50


class RefineGrnaRequest(BaseModel):
    grnaSequence: str
    newLength: int
    snpPosition: int
    referenceContext: str


class GrnaCandidate(BaseModel):
    id: int
    sequence: str
    pamSite: str
    pamPosition: int
    cutSiteDistance: int
    gcContent: float
    homopolymerPenalty: float
    offTargetCount: int
    score: float
    editType: str   # "Base Edit" | "HDR"
    strand: str     # "sense" | "antisense"


class CrisprDesignResponse(BaseModel):
    grnaCandidates: List[GrnaCandidate]


class RefineGrnaResponse(BaseModel):
    refinedGRNA: Optional[GrnaCandidate]
    previousScore: float
    improvement: float


# ── Binding Site ──────────────────────────────────────────────────────────────

class BindingSiteRequest(BaseModel):
    grna: Dict[str, Any]
    snp: Dict[str, Any]
    windowSize: Optional[int] = 100


class BindingSiteResponse(BaseModel):
    referenceWindow: str
    complementaryStrand: str
    startPosition: int
    endPosition: int
    grnaBindStart: int
    grnaBindEnd: int
    pamStart: int
    pamEnd: int
    snpPositionInWindow: int
    cutSitePosition: int
