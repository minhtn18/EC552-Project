"""
crispr_logic.py — CRISPR guide RNA design helpers.

Provides:
  - find_grna_candidates()  PAM detection, guide extraction, scoring
  - refine_guide()          Trim/extend a guide to a new length and re-score
  - compute_binding_site()  Locate guide in reference, extract window coordinates

All scoring is done locally using the existing BLAST+ binary (already configured).
No external CRISPR API or library is required.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# Available after paths.py adds BLAST_ROOT to sys.path (imported by routes before this module)
from Blast_code import (
    fetch_all_blast_records,
    normalize_sequence,
    parse_blast_tabular,
    write_single_fasta,
)

GUIDE_LENGTH = 20
CUT_OFFSET = 3          # Cas9 cuts 3 bp upstream of the PAM (between guide pos 17/18)
MAX_GUIDE_LENGTH = 25
MIN_GUIDE_LENGTH = 17

_COMPLEMENT = str.maketrans("ACGT", "TGCA")

_TRANSITIONS = {("A", "G"), ("G", "A"), ("C", "T"), ("T", "C")}


# ── Sequence utilities ────────────────────────────────────────────────────────

def reverse_complement(seq: str) -> str:
    return seq.upper().translate(_COMPLEMENT)[::-1]


def _max_homopolymer_run(seq: str) -> int:
    """Return the length of the longest run of a single nucleotide."""
    if not seq:
        return 0
    max_run = current = 1
    for i in range(1, len(seq)):
        current = current + 1 if seq[i] == seq[i - 1] else 1
        if current > max_run:
            max_run = current
    return max_run


def _edit_type(ref_nuc: str, var_nuc: str) -> str:
    """
    Transitions (A↔G, C↔T) are amenable to base editing (ABE/CBE).
    Transversions require HDR.
    """
    return "Base Edit" if (ref_nuc.upper(), var_nuc.upper()) in _TRANSITIONS else "HDR"


# ── Short-query BLAST helper ──────────────────────────────────────────────────

def _run_blastn_short(
    query_fasta: Path,
    db_name: str,
    output_file: Path,
    blast_bin: str,
    workdir: Path,
) -> subprocess.CompletedProcess:
    """
    Run blastn tuned for short queries (≤30 bp gRNA guides).

    -task blastn-short  automatically lowers word_size (to 7) and evalue for short seqs
    -dust no            disables low-complexity masking — essential for 20-mers
    -evalue 1000        permissive threshold so near-matches are not discarded early
    """
    cmd = [
        str(Path(blast_bin) / "blastn.exe"),
        "-query",  str(query_fasta),
        "-db",     str(db_name),
        "-out",    str(output_file),
        "-outfmt", "6",
        "-task",   "blastn-short",
        "-dust",   "no",
        "-evalue", "1000",
    ]
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(workdir))


# ── Off-target counting via BLAST ─────────────────────────────────────────────

def _count_off_targets(
    guide: str,
    blast_bin: str,
    db_name: str,
    workdir: Path,
) -> int:
    """
    Run blastn-short with the 20-mer guide as query against the reference DB.
    Count near-match hits (≤ 3 mismatches, no gaps), excluding the perfect match.

    Uses _run_blastn_short() so that the short-sequence parameters are applied;
    the default run_blastn() uses word_size=11 which misses near-matches in 20-mers.
    """
    with tempfile.TemporaryDirectory(dir=workdir) as tmp:
        tmp_path = Path(tmp)
        query_fasta = tmp_path / "guide.fasta"
        results_file = tmp_path / "guide_results.txt"
        write_single_fasta("guide_query", guide, query_fasta)

        result = _run_blastn_short(query_fasta, db_name, results_file, blast_bin, workdir)
        if result.returncode != 0:
            return 0

        count = 0
        for row in parse_blast_tabular(results_file):
            try:
                mismatches = int(row.get("mismatch", 99))
                gaps = int(row.get("gapopen", 99))
            except (ValueError, TypeError):
                continue
            # Near-match: ≤ 3 mismatches, no gaps, not a perfect hit
            if gaps == 0 and 0 < mismatches <= 3:
                count += 1
    return count


# ── Guide locator for binding site ───────────────────────────────────────────

def _blast_locate_guide(
    guide: str,
    blast_bin: str,
    db_name: str,
    workdir: Path,
) -> Optional[Dict]:
    """
    Use blastn-short to find the guide's binding position in the reference DB.
    Tolerates up to 3 mismatches (covers the 1-base patient/reference SNP difference).

    Returns the best hit row dict (keys: sseqid, sstart, send, mismatch, sstrand, ...)
    or None if the guide cannot be located.
    """
    with tempfile.TemporaryDirectory(dir=workdir) as tmp:
        tmp_path = Path(tmp)
        query_fasta = tmp_path / "locate.fasta"
        results_file = tmp_path / "locate_results.txt"
        write_single_fasta("guide_query", guide, query_fasta)

        result = _run_blastn_short(query_fasta, db_name, results_file, blast_bin, workdir)
        if result.returncode != 0:
            return None

        rows = parse_blast_tabular(results_file)
        if not rows:
            return None

        # Pick the best hit by bitscore; discard hits with > 3 mismatches
        best = max(rows, key=lambda r: float(r.get("bitscore", 0)))
        if int(best.get("mismatch", 99)) > 3:
            return None
        return best


# ── Composite scoring ─────────────────────────────────────────────────────────

def _cheap_score(
    guide: str,
    pam_position: int,  # 0-based index in sequence where PAM starts
    snp_position: int,  # 0-based index in surrounding_sequence
) -> Dict:
    """
    Compute the three fast metrics (GC content, cut-site proximity, homopolymer
    penalty) without running any BLAST search.  Used to pre-rank candidates so
    the expensive off-target BLAST only runs on the top N guides.
    """
    gc = (guide.count("G") + guide.count("C")) / len(guide) * 100
    cut_dist = abs(snp_position - (pam_position - CUT_OFFSET))
    hp = _max_homopolymer_run(guide) / len(guide)

    gc_score  = 1.0 if 40 <= gc <= 65 else 0.5
    cut_score = max(0.0, 1.0 - cut_dist / 20.0)
    hp_score  = 1.0 - hp

    # Off-target weight reserved at 0 so we can add it later; partial score used
    # only for pre-ranking, not returned to the caller.
    partial = 0.30 * cut_score + 0.25 * gc_score + 0.15 * hp_score

    return {
        "gcContent":          round(gc, 1),
        "cutSiteDistance":    cut_dist,
        "homopolymerPenalty": round(hp, 4),
        "_partial":           partial,  # internal pre-rank key, stripped later
    }


def _finalise_score(candidate: Dict, blast_bin: str, db_name: str, workdir: Path) -> Dict:
    """
    Add off-target count via BLAST and compute the final composite score.
    Call this only on pre-filtered candidates to avoid running BLAST on every
    PAM site found in the surrounding sequence.
    """
    guide = candidate["sequence"]
    off_targets = _count_off_targets(guide, blast_bin, db_name, workdir)

    gc_score  = 1.0 if 40 <= candidate["gcContent"] <= 65 else 0.5
    cut_score = max(0.0, 1.0 - candidate["cutSiteDistance"] / 20.0)
    hp_score  = 1.0 - candidate["homopolymerPenalty"]
    ot_score  = max(0.0, 1.0 - off_targets / 10.0)

    score = (
        0.30 * cut_score +
        0.25 * gc_score  +
        0.15 * hp_score  +
        0.30 * ot_score
    )

    candidate.pop("_partial", None)
    candidate["offTargetCount"] = off_targets
    candidate["score"] = round(score, 4)
    return candidate


def _score_guide(
    guide: str,
    pam_position: int,
    snp_position: int,
    blast_bin: str,
    db_name: str,
    workdir: Path,
) -> Dict:
    """
    Full composite score (cheap metrics + BLAST off-target count) for a single guide.
    Used by refine_guide() and the refine-grna route where only one guide is scored
    at a time, so the two-phase pre-filter optimisation is not needed.
    """
    candidate = {
        "sequence": guide,
        **_cheap_score(guide, pam_position, snp_position),
    }
    _finalise_score(candidate, blast_bin, db_name, workdir)
    return candidate


# ── Public API ────────────────────────────────────────────────────────────────

def find_grna_candidates(
    surrounding_sequence: str,
    snp_position: int,       # 0-based index within surrounding_sequence
    ref_nucleotide: str,
    var_nucleotide: str,
    blast_bin: str,
    db_name: str,
    workdir: Path,
    max_candidates: int = 10,
) -> List[Dict]:
    """
    Scan both strands of surrounding_sequence for NGG PAM sites, extract 20-mer
    guide RNAs, score each by the composite metric, and return the top candidates
    sorted by score descending.

    Two-phase scoring to avoid running BLAST on every PAM site:
      Phase 1 — cheap metrics only (GC, cut distance, homopolymer): O(1) per guide.
      Phase 2 — BLAST off-target count: only for the top 2× max_candidates guides
                 from phase 1, limiting BLAST calls to ≤ 2*max_candidates.

    Sense strand:     [20-mer guide][NGG]
    Antisense strand: [CCN][20-mer guide on RC strand]
    """
    seq = normalize_sequence(surrounding_sequence)
    edit_type = _edit_type(ref_nucleotide, var_nucleotide)
    pool: List[Dict] = []
    guide_id = 1

    # ── Phase 1: collect all PAM sites and compute cheap scores ──────────────

    # Sense strand (search for xGG)
    for p in range(GUIDE_LENGTH, len(seq) - 2):
        if seq[p + 1] == "G" and seq[p + 2] == "G":
            guide = seq[p - GUIDE_LENGTH:p]
            if len(guide) != GUIDE_LENGTH or "N" in guide:
                continue
            cheap = _cheap_score(guide, p, snp_position)
            pool.append({
                "id":          guide_id,
                "sequence":    guide,
                "pamSite":     seq[p:p + 3],
                "pamPosition": p,
                "strand":      "sense",
                "editType":    edit_type,
                **cheap,
            })
            guide_id += 1

    # Antisense strand (RC of sequence, then same NGG scan)
    rc_seq = reverse_complement(seq)
    rc_len = len(rc_seq)
    for p in range(GUIDE_LENGTH, rc_len - 2):
        if rc_seq[p + 1] == "G" and rc_seq[p + 2] == "G":
            guide = rc_seq[p - GUIDE_LENGTH:p]
            if len(guide) != GUIDE_LENGTH or "N" in guide:
                continue
            sense_pam_pos = rc_len - p - 3  # map back to sense-strand coordinate
            cheap = _cheap_score(guide, sense_pam_pos, snp_position)
            pool.append({
                "id":          guide_id,
                "sequence":    guide,
                "pamSite":     rc_seq[p:p + 3],
                "pamPosition": sense_pam_pos,
                "strand":      "antisense",
                "editType":    edit_type,
                **cheap,
            })
            guide_id += 1

    # ── Phase 2: run BLAST off-target count on the best candidates only ───────
    # Pre-rank by partial score (no off-target term yet) and limit BLAST calls
    # to 2× max_candidates so the endpoint stays well within the request timeout.
    pool.sort(key=lambda c: c["_partial"], reverse=True)
    blast_budget = max_candidates * 2
    for candidate in pool[:blast_budget]:
        _finalise_score(candidate, blast_bin, db_name, workdir)

    # Candidates outside the budget still need their fields set (score = partial,
    # offTargetCount = 0) so the response model is always complete.
    for candidate in pool[blast_budget:]:
        candidate.pop("_partial", None)
        candidate.setdefault("offTargetCount", 0)
        candidate.setdefault("score", 0.0)

    # Final sort and truncate
    pool.sort(key=lambda c: c["score"], reverse=True)
    top = pool[:max_candidates]
    for i, c in enumerate(top, start=1):
        c["id"] = i
    return top


def refine_guide(
    grna_sequence: str,
    new_length: int,
    reference_context: str,
    snp_position: int,
    blast_bin: str,
    db_name: str,
    workdir: Path,
) -> Optional[Dict]:
    """
    Trim or extend a guide RNA to new_length bases, then re-score.

    Trimming removes from the 5' end (PAM-distal), preserving PAM proximity.
    Extension prepends bases from reference_context at the 5' end.
    Returns None if the adjusted guide contains Ns or is otherwise invalid.
    """
    current = normalize_sequence(grna_sequence)
    ref_ctx = normalize_sequence(reference_context) if reference_context else ""
    new_length = max(MIN_GUIDE_LENGTH, min(MAX_GUIDE_LENGTH, new_length))

    if new_length < len(current):
        # Trim from 5' end — keep the PAM-proximal 3' portion
        refined = current[len(current) - new_length:]
    elif new_length > len(current):
        # Extend from 5' end using reference context
        needed = new_length - len(current)
        extension = ref_ctx[-needed:] if len(ref_ctx) >= needed else ref_ctx
        refined = (extension + current)[-new_length:]
    else:
        refined = current

    if "N" in refined or len(refined) < MIN_GUIDE_LENGTH:
        return None

    scores = _score_guide(refined, len(refined), snp_position, blast_bin, db_name, workdir)
    return {
        "id":                 0,
        "sequence":           refined,
        "pamSite":            "NGG",
        "pamPosition":        0,
        "strand":             "sense",
        "editType":           "Base Edit",
        **scores,
    }


def compute_binding_site(
    guide_sequence: str,
    strand: str,
    snp_position: int,
    blast_bin: str,
    db_name: str,
    workdir: Path,
    window_size: int = 100,
) -> Optional[Dict]:
    """
    Find the guide sequence in the first reference DB record, extract a window
    of window_size bases around the binding site, and return relative coordinates
    for the SVG genome viewer (grnaBindStart/End, pamStart/End, cutSitePosition,
    snpPositionInWindow, complementaryStrand).

    Returns None if the guide cannot be located in the reference.
    """
    records = fetch_all_blast_records(db_name=db_name, blast_bin=blast_bin, workdir=str(workdir))
    if not records:
        return None

    ref_seq = normalize_sequence(records[0].sequence)

    # Use BLAST (not str.find) so we tolerate the 1-base patient/reference mismatch
    # at the SNP position — guides designed from the patient sequence will differ
    # from the reference by exactly 1 base at the SNP site.
    hit = _blast_locate_guide(guide_sequence, blast_bin, db_name, workdir)
    if hit is None:
        return None

    # BLAST sstart/send are 1-based; convert to 0-based Python indices.
    # When the hit is on the minus strand sstart > send, so normalise.
    s1 = int(hit.get("sstart", 1)) - 1
    s2 = int(hit.get("send",   1)) - 1
    bind_start = min(s1, s2)
    bind_end   = max(s1, s2) + 1   # exclusive end

    # Keep strand consistent with BLAST result
    if hit.get("sstrand", strand) == "minus":
        strand = "antisense"
    pam_start = bind_end           # NGG sits immediately 3' of the guide
    pam_end   = pam_start + 3
    cut_pos   = bind_end - CUT_OFFSET

    # Extract window centered on the binding region
    center    = (bind_start + bind_end) // 2
    win_start = max(0, center - window_size // 2)
    win_end   = min(len(ref_seq), win_start + window_size)
    win_start = max(0, win_end - window_size)   # re-anchor if near end of sequence

    ref_window = ref_seq[win_start:win_end]

    # Clamp SNP position to be relative to window
    snp_in_win = max(0, min(snp_position - win_start, len(ref_window) - 1))

    return {
        "referenceWindow":    ref_window,
        "complementaryStrand": reverse_complement(ref_window),
        "startPosition":      win_start,
        "endPosition":        win_end,
        "grnaBindStart":      max(0, bind_start - win_start),
        "grnaBindEnd":        min(len(ref_window), bind_end - win_start),
        "pamStart":           max(0, pam_start - win_start),
        "pamEnd":             min(len(ref_window), pam_end - win_start),
        "snpPositionInWindow": snp_in_win,
        "cutSitePosition":    max(0, cut_pos - win_start),
    }
