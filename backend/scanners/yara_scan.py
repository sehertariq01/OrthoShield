"""
Fix 2: YARA scanner now reports scanner_available=False when the yara binary
is unreachable (WSL down, binary missing) instead of silently passing.
"""
import subprocess
import os


def _compute_wsl_path(windows_path: str) -> str:
    """Convert a Windows absolute path to its WSL /mnt/... equivalent."""
    abs_path = os.path.abspath(windows_path)
    drive, rest = os.path.splitdrive(abs_path)
    drive_letter = drive.replace(":", "").lower()
    rest = rest.replace("\\", "/")
    return f"/mnt/{drive_letter}{rest}"


# Resolve the YARA rules file path at import time so it works regardless
# of which drive or directory the project is installed in.
RULES_PATH_WSL = _compute_wsl_path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "yara_rules.yar")
)


def windows_path_to_wsl(file_path: str) -> str:
    abs_path = os.path.abspath(file_path)
    drive, rest = os.path.splitdrive(abs_path)
    drive_letter = drive.replace(":", "").lower()
    rest = rest.replace("\\", "/")
    return f"/mnt/{drive_letter}{rest}"


def scan_file_with_yara(file_path: str) -> dict:
    """
    Check 11: Pattern-based detection via custom YARA rules running in WSL.
    Returns scanner_available=False when WSL or the yara binary is unavailable,
    so the scoring engine can fail closed rather than silently passing.
    """
    result = {
        "name": "yara_scan",
        "passed": True,
        "scanner_available": True,
        "detail": "",
    }

    try:
        wsl_path = windows_path_to_wsl(file_path)

        proc = subprocess.run(
            ["wsl", "yara", RULES_PATH_WSL, wsl_path],
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Non-zero return code with output on stderr usually means yara/WSL unavailable
        if proc.returncode not in (0, 1) and proc.stderr:
            result["scanner_available"] = False
            result["detail"] = f"YARA unavailable: {proc.stderr.strip()[:200]}"
            return result

        output = proc.stdout.strip()

        if not output:
            result["detail"] = "No YARA rule matches (clean)"
        else:
            matched_rules = [line.split(" ")[0] for line in output.splitlines() if line.strip()]
            result["passed"] = False
            result["detail"] = f"YARA rule(s) matched: {', '.join(matched_rules)}"

    except subprocess.TimeoutExpired:
        result["scanner_available"] = False
        result["detail"] = "YARA scan timed out"
    except FileNotFoundError:
        # wsl binary not found on this machine
        result["scanner_available"] = False
        result["detail"] = "WSL not found — YARA scanner unavailable"
    except Exception as e:
        result["scanner_available"] = False
        result["detail"] = f"YARA scan error: {e}"

    return result