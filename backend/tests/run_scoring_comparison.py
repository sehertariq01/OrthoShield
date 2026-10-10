"""
Scoring comparison test runner
==============================
Runs every DICOM in datasets/ through both the old scoring engine (Tier 1
denominator = 178, duplicate_detection) and the new scoring engine (Fix 4/5
denominator = ran-checks only, replay_detection), then writes
backend/tests/scoring_comparison.md with:

  filename | old_score | new_score | old_decision | new_decision | flipped | notes

Usage:
    python backend/tests/run_scoring_comparison.py

All scanners that require external processes (ClamAV, YARA, VirusTotal)
are stubbed so this is reproducible offline. The comparison isolates the
pure scoring-maths change.
"""
import os
import sys
import hashlib
import json
from pathlib import Path

# ── path setup so we can import backend modules directly ─────────────────────
BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND))

from scanners.dicom_parser   import parse_dicom_metadata
from scanners.rule_checks    import (
    check_magic_byte_and_structure,
    check_path_traversal,
    check_file_size,
    check_required_tags,
    check_uid_format,
    check_study_date,
    check_pixel_data_consistency,
    check_injection_patterns,
)
from scanners.ml_anomaly     import check_ml_anomaly
from scanners.embedded_extractor import check_embedded_objects

# ── Stub scanners (require external processes) ────────────────────────────────
def _stub_passed(name):
    return {"name": name, "passed": True, "scanner_available": True, "skipped": False, "detail": "stubbed"}

def stub_clamav(fp):      return _stub_passed("malware_scan")
def stub_yara(fp):        return _stub_passed("yara_scan")
def stub_virustotal(fh):  return _stub_passed("virustotal")

# ── Stub replay/duplicate (no DB in test) ─────────────────────────────────────
def stub_replay():
    return {"name": "replay_detection", "passed": True, "scanner_available": True, "skipped": False, "is_duplicate": False, "detail": "stubbed"}

def stub_duplicate():
    return {"name": "duplicate_detection", "passed": True, "scanner_available": True, "detail": "stubbed"}

# ── Old scoring engine (Tier 1 state) ────────────────────────────────────────
OLD_WEIGHTS = {
    "malware_scan": 30, "virustotal": 25, "yara_scan": 20,
    "embedded_objects": 20, "ml_anomaly_score": 15, "magic_byte_structure": 15,
    "duplicate_detection": 10, "path_traversal": 10, "injection_patterns": 8,
    "required_tags": 5, "uid_format": 5, "timestamp_validity": 5,
    "pixel_data_consistency": 5, "file_size_limit": 5,
}
OLD_HARD_BLOCK = {"magic_byte_structure", "malware_scan", "yara_scan", "virustotal"}
OLD_DENOMINATOR = sum(OLD_WEIGHTS.values())   # = 178
OLD_THRESHOLD_POINTS = 25                     # raw points

def old_score(checks):
    pts = 0
    hard = False
    for c in checks:
        name = c.get("name") or c.get("check")
        if not c.get("passed", True):
            w = OLD_WEIGHTS.get(name, 5)
            pts += w
            if name in OLD_HARD_BLOCK:
                hard = True
    rs = round((pts / OLD_DENOMINATOR) * 100, 2)
    dec = "BLOCKED" if (pts >= OLD_THRESHOLD_POINTS or hard) else "CLEAN"
    return rs, dec

# ── New scoring engine (Fix 4 + 5) ───────────────────────────────────────────
NEW_WEIGHTS = {
    "malware_scan": 30, "virustotal": 25, "yara_scan": 20,
    "embedded_objects": 20, "ml_anomaly_score": 15, "magic_byte_structure": 15,
    "replay_detection": 15, "path_traversal": 10, "injection_patterns": 8,
    "required_tags": 5, "uid_format": 5, "timestamp_validity": 5,
    "pixel_data_consistency": 5, "file_size_limit": 5,
}
NEW_HARD_BLOCK = {"magic_byte_structure", "malware_scan", "yara_scan", "virustotal", "path_traversal", "replay_detection"}
NEW_THRESHOLD_PCT = 15   # set after corpus analysis; re-tune post Fix 6

def new_score(checks):
    ran = [c for c in checks if c.get("scanner_available", True) and not c.get("skipped", False)]
    denom = sum(NEW_WEIGHTS.get(c["name"], 5) for c in ran) or 1
    pts = 0
    hard = False
    for c in ran:
        name = c.get("name")
        if not c.get("passed", True):
            w = NEW_WEIGHTS.get(name, 5)
            pts += w
            if name in NEW_HARD_BLOCK:
                hard = True
    rs = round((pts / denom) * 100, 2)
    dec = "BLOCKED" if (pts > 0 and (hard or rs >= NEW_THRESHOLD_PCT)) else "CLEAN"
    return rs, dec, denom

# ── Build check list for a file ───────────────────────────────────────────────
def run_checks_for_file(dcm_path: Path):
    """Return two lists: old_checks (duplicate) and new_checks (replay)."""
    metadata   = parse_dicom_metadata(str(dcm_path))
    file_size  = dcm_path.stat().st_size
    filename   = dcm_path.name

    shared = [
        check_magic_byte_and_structure(metadata),
        check_path_traversal(filename),
        check_file_size(file_size),
    ]
    if metadata.get("is_valid_dicom", False):
        shared += [
            check_required_tags(metadata),
            check_uid_format(metadata),
            check_study_date(metadata),
            check_pixel_data_consistency(metadata),
            check_injection_patterns(metadata),
        ]

    dynamic = [
        stub_clamav(str(dcm_path)),
        stub_yara(str(dcm_path)),
        stub_virustotal(""),
        check_ml_anomaly(str(dcm_path), metadata),
        check_embedded_objects(str(dcm_path), metadata),
    ]

    old_checks = shared + dynamic + [stub_duplicate()]
    new_checks = shared + dynamic + [stub_replay()]
    return old_checks, new_checks

# ── Collect all DICOM files ───────────────────────────────────────────────────
DATASETS_DIR = BACKEND.parent / "datasets"
dcm_files = sorted(DATASETS_DIR.rglob("*.dcm"))

print(f"Found {len(dcm_files)} DICOM files in {DATASETS_DIR}")

# ── Run ───────────────────────────────────────────────────────────────────────
rows = []
scores_for_distribution = []

for dcm_path in dcm_files:
    rel = dcm_path.relative_to(DATASETS_DIR.parent)
    try:
        old_checks, new_checks = run_checks_for_file(dcm_path)
    except Exception as e:
        rows.append({
            "filename": str(rel),
            "old_score": "ERROR", "new_score": "ERROR",
            "old_decision": "ERROR", "new_decision": "ERROR",
            "flipped": False, "notes": str(e),
        })
        continue

    os_, od = old_score(old_checks)
    ns, nd, denom = new_score(new_checks)

    flipped = od != nd
    notes_parts = []

    if flipped:
        notes_parts.append(f"**DECISION FLIP** {od}→{nd}")

    # explain non-trivial score changes
    delta = round(ns - os_, 2) if isinstance(ns, float) and isinstance(os_, float) else None
    if delta is not None and abs(delta) > 5:
        notes_parts.append(f"score Δ={delta:+.1f} (denom={denom})")

    # flag hard-block triggers
    old_failed = [c["name"] for c in old_checks if not c.get("passed", True)]
    new_failed = [c["name"] for c in new_checks if not c.get("skipped", False) and not c.get("passed", True)]
    if old_failed or new_failed:
        notes_parts.append(f"old_failed={old_failed} new_failed={new_failed}")

    rows.append({
        "filename":     str(rel),
        "old_score":    os_,
        "new_score":    ns,
        "old_decision": od,
        "new_decision": nd,
        "flipped":      flipped,
        "notes":        " | ".join(notes_parts) if notes_parts else "—",
    })
    if isinstance(ns, float):
        scores_for_distribution.append(ns)

# ── Score distribution buckets ───────────────────────────────────────────────
buckets = {"0": 0, "1-5": 0, "6-10": 0, "11-15": 0, "16-20": 0, "21-30": 0, "31-50": 0, "51-100": 0}
for s in scores_for_distribution:
    if s == 0:
        buckets["0"] += 1
    elif s <= 5:
        buckets["1-5"] += 1
    elif s <= 10:
        buckets["6-10"] += 1
    elif s <= 15:
        buckets["11-15"] += 1
    elif s <= 20:
        buckets["16-20"] += 1
    elif s <= 30:
        buckets["21-30"] += 1
    elif s <= 50:
        buckets["31-50"] += 1
    else:
        buckets["51-100"] += 1

# ── Write markdown ────────────────────────────────────────────────────────────
OUT_PATH = BACKEND / "tests" / "scoring_comparison.md"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

flipped_rows = [r for r in rows if r["flipped"]]
total        = len(rows)
errors       = sum(1 for r in rows if r["old_score"] == "ERROR")

with open(OUT_PATH, "w", encoding="utf-8") as md:
    md.write("# Scoring Comparison Report — Fix 4 + Fix 5\n\n")
    md.write(f"> Generated from `{len(dcm_files)}` DICOM files in `datasets/`\n\n")
    md.write("## Summary\n\n")
    md.write(f"| Metric | Value |\n|--------|-------|\n")
    md.write(f"| Files scanned | {total} |\n")
    md.write(f"| Errors (could not parse) | {errors} |\n")
    md.write(f"| Decision flips | {len(flipped_rows)} |\n\n")

    md.write("## Score Distribution (new engine)\n\n")
    md.write("> **You must choose `BLOCK_THRESHOLD` from this table.**\n")
    md.write("> Files ≥ threshold will be BLOCKED (excluding hard-blocks which always block).\n\n")
    md.write("| New score range | File count | % of total |\n")
    md.write("|-----------------|-----------|------------|\n")
    valid_total = total - errors
    for label, count in buckets.items():
        pct = round(100 * count / valid_total, 1) if valid_total > 0 else 0
        md.write(f"| {label} | {count} | {pct}% |\n")
    if scores_for_distribution:
        md.write(f"\n**Min:** {min(scores_for_distribution):.2f} &nbsp; ")
        md.write(f"**Max:** {max(scores_for_distribution):.2f} &nbsp; ")
        md.write(f"**Mean:** {sum(scores_for_distribution)/len(scores_for_distribution):.2f} &nbsp; ")
        sorted_s = sorted(scores_for_distribution)
        mid = len(sorted_s) // 2
        median = sorted_s[mid] if len(sorted_s) % 2 else (sorted_s[mid-1] + sorted_s[mid]) / 2
        md.write(f"**Median:** {median:.2f}\n\n")

    md.write("## Decision Flips\n\n")
    if flipped_rows:
        md.write("| Filename | Old score | New score | Old decision | New decision | Notes |\n")
        md.write("|----------|-----------|-----------|--------------|--------------|-------|\n")
        for r in flipped_rows:
            md.write(
                f"| `{r['filename']}` | {r['old_score']} | {r['new_score']} "
                f"| {r['old_decision']} | {r['new_decision']} | {r['notes']} |\n"
            )
    else:
        md.write("_No decision flips — all files produced the same CLEAN/BLOCKED outcome under both engines._\n")
    md.write("\n")

    md.write("## Full Results\n\n")
    md.write("| Filename | Old score | New score | Old decision | New decision | Flipped | Notes |\n")
    md.write("|----------|-----------|-----------|--------------|--------------|---------|-------|\n")
    for r in rows:
        flip_mark = "⚠️ YES" if r["flipped"] else "no"
        md.write(
            f"| `{r['filename']}` | {r['old_score']} | {r['new_score']} "
            f"| {r['old_decision']} | {r['new_decision']} | {flip_mark} | {r['notes']} |\n"
        )

print(f"\nReport written to: {OUT_PATH}")
print(f"Decision flips: {len(flipped_rows)}/{total}")
print("\nScore distribution (new engine):")
for label, count in buckets.items():
    pct = round(100 * count / (valid_total or 1), 1)
    bar = "#" * (count // max(1, (valid_total // 40)))
    print(f"  {label:>8}: {count:>4}  {pct:>5}%  {bar}")
