"""
Fix 4 (Tier 2) + Tier 1 correction:

Tier 1 correction:
  - Exclude skipped=True checks from denominator (they have no result to score).

Fix 4 — scoring denominator now uses only the checks that actually ran:
  denominator = sum of weights for checks where scanner_available=True
                AND skipped != True
  This means one failed non-critical check out of ten is ~10%, not 3%.
  The old denominator (178 = sum of ALL weights) made most thresholds
  unreachable without a hard-block.

Fix 4 — path_traversal promoted to HARD_BLOCK:
  There is no benign reason for ../ in a medical filename.

Fix 5 — duplicate_detection renamed to replay_detection (weight 15):
  Only fires on same SOPInstanceUID with different bytes (tamper/replay).
  Benign hash-duplicate resends set is_duplicate=True but passed=True
  and are excluded from scoring entirely via skipped=True.

BLOCK_THRESHOLD is intentionally left as a named constant so the operator
can tune it after reviewing the score distribution report.
"""

CHECK_WEIGHTS = {
    # External AV / reputation engines
    "malware_scan":          30,
    "virustotal":            25,
    "yara_scan":             20,
    # Byte / content analysis
    "embedded_objects":      20,
    "ml_anomaly_score":      15,
    # Structural / identity checks
    "magic_byte_structure":  15,
    "replay_detection":      15,   # Fix 5: was duplicate_detection (weight 10)
    "path_traversal":        10,
    "injection_patterns":     8,
    "required_tags":          5,
    "uid_format":             5,
    "timestamp_validity":     5,
    "pixel_data_consistency": 5,
    "file_size_limit":        5,
}

# Hard-block: file is BLOCKED immediately regardless of total score.
# Fix 4: path_traversal added — no benign reason for ../ in a medical filename.
# Tier 2 enhancement: replay_detection added — same SOPInstanceUID with altered bytes
# indicates study tampering or corrupted retransmission.
HARD_BLOCK_CHECKS = {
    "magic_byte_structure",
    "malware_scan",
    "yara_scan",
    "virustotal",
    "path_traversal",        # Fix 4: promoted
    "replay_detection",      # Confirmed study tampering / UID collision
}

# "quarantine"  → fail closed: any offline scanner blocks the file
# "flag"        → fail open: allow but mark incomplete_scan=True
DEGRADED_MODE = "quarantine"

# ── Operator-tunable threshold ────────────────────────────────────────────────
# PROVISIONAL — ml_anomaly_score is skipped on 100 % of the current corpus
# because no model has been trained yet, so this distribution reflects only
# 13 active checks (not 14).  Re-tune this value after Fix 6 trains
# per-modality Isolation Forest models and the 14th check starts producing
# real scores.
#
# Distribution snapshot (145 files, 13 active checks):
#   score=0     71 files (49 %)
#   score 1-5   25 files (17 %)
#   score 6-10   5 files  (3 %)
#   score 11-15 25 files (17 %)   ← this band shifts after Fix 6
#   score 16-20 17 files (12 %)
#   score 21-30  2 files  (1 %)
BLOCK_THRESHOLD = 15   # provisional; re-tune post Fix 6


def calculate_risk_score(check_results: list) -> dict:
    """
    Weighted risk score with a per-scan denominator.

    Denominator = sum of weights for checks that:
      (a) had scanner_available=True, AND
      (b) were not skipped (skipped=True)

    This means the score reflects reality: if ClamAV ran and found nothing,
    that 30-point check contributes to the denominator.  If ml_anomaly was
    skipped because no model is trained, its 15 points do not dilute the score.
    """
    # ── Step 1: fail closed on unavailable scanners ───────────────────────────
    unavailable = [c["name"] for c in check_results if not c.get("scanner_available", True)]

    if unavailable and DEGRADED_MODE == "quarantine":
        return {
            "risk_score":          None,
            "risk_points":         None,
            "decision":            "BLOCKED",
            "reason":              f"Scan incomplete — engines offline: {', '.join(unavailable)}",
            "incomplete_scan":     True,
            "unavailable_engines": unavailable,
            "failed_checks":       [],
        }

    # ── Step 2: identify checks that produced a meaningful result ─────────────
    # skipped=True → no result, exclude from denominator AND from scoring
    ran = [
        c for c in check_results
        if c.get("scanner_available", True) and not c.get("skipped", False)
    ]

    # Fix 4: denominator is the sum of weights of checks that actually ran —
    # not the global constant sum of all possible check weights.
    denominator = sum(CHECK_WEIGHTS.get(c["name"], 5) for c in ran) or 1

    risk_points   = 0
    failed_checks = []
    hard_block    = False
    hard_block_names = []

    for c in ran:
        name = c.get("name")
        if not c.get("passed", True):
            weight = CHECK_WEIGHTS.get(name, 5)
            risk_points += weight
            failed_checks.append({
                "name":   name,
                "weight": weight,
                "detail": c.get("detail", ""),
            })
            if name in HARD_BLOCK_CHECKS:
                hard_block = True
                hard_block_names.append(name)

    risk_score = round((risk_points / denominator) * 100, 2)

    if hard_block:
        decision = "BLOCKED"
        reason   = f"Hard-block check failed: {', '.join(hard_block_names)}"
    elif risk_score >= BLOCK_THRESHOLD:
        decision = "BLOCKED"
        reason   = f"Risk score {risk_score} >= threshold {BLOCK_THRESHOLD}"
    else:
        decision = "CLEAN"
        reason   = f"Risk score {risk_score} < threshold {BLOCK_THRESHOLD}"

    return {
        "risk_score":          risk_score,
        "risk_points":         risk_points,
        "denominator":         denominator,
        "decision":            decision,
        "reason":              reason,
        "incomplete_scan":     False,
        "unavailable_engines": unavailable,
        "failed_checks":       failed_checks,
    }