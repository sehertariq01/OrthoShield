"""
Fix 1: Hash-only VirusTotal lookup.
The file body is NEVER transmitted — DICOM files contain PHI and uploading
them to a public third-party service is a disclosure event.
"""
import requests
from config import VT_API_KEY

VT_URL = "https://www.virustotal.com/api/v3/files/{}"


def check_virustotal(file_hash: str) -> dict:
    """
    Check 13 (Static reputation lookup): Query VirusTotal for a prior verdict
    on this file hash.  We do NOT upload the file — a 404 (hash unknown) is the
    normal result for a private hospital study and is not a finding.
    """
    result = {
        "name": "virustotal",
        "passed": True,
        "scanner_available": True,
        "detail": "",
    }

    if not VT_API_KEY:
        result["scanner_available"] = False
        result["detail"] = "VT_API_KEY not configured"
        return result

    try:
        r = requests.get(
            VT_URL.format(file_hash),
            headers={"x-apikey": VT_API_KEY},
            timeout=15,
        )
    except requests.RequestException as e:
        result["scanner_available"] = False
        result["detail"] = f"VirusTotal unreachable: {e}"
        return result

    if r.status_code == 404:
        # Hash unknown to VT — normal for private hospital studies.
        # Do NOT upload the file.
        result["detail"] = "Hash not previously seen by VirusTotal (expected for private studies)"
        return result

    if r.status_code == 429:
        result["scanner_available"] = False
        result["detail"] = "VirusTotal rate limit reached"
        return result

    if r.status_code != 200:
        result["scanner_available"] = False
        result["detail"] = f"VirusTotal returned HTTP {r.status_code}"
        return result

    stats = r.json()["data"]["attributes"]["last_analysis_stats"]
    malicious  = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    total      = sum(stats.values())

    if malicious > 0 or suspicious > 2:
        result["passed"] = False
        result["detail"] = f"{malicious} malicious / {suspicious} suspicious of {total} engines"
    else:
        result["detail"] = f"0/{total} engines flagged"

    return result
