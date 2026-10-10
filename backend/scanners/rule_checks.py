"""
All rule checks updated to return the canonical result shape:
  {name, passed, scanner_available, detail}
scanner_available is always True for these pure-Python checks.
"""
import re
from datetime import datetime

REQUIRED_TAGS = [
    "sop_instance_uid",
    "sop_class_uid",
    "modality",
    "rows",
    "columns",
]


def _result(name: str, passed: bool, detail: str) -> dict:
    """Build a canonical check result. scanner_available is always True here."""
    return {"name": name, "passed": passed, "scanner_available": True, "detail": detail}


def check_magic_byte_and_structure(metadata: dict) -> dict:
    """Check 1: Was the file parseable as a valid DICOM file?"""
    if not metadata.get("is_valid_dicom", False):
        return _result(
            "magic_byte_structure", False,
            metadata.get("error", "Invalid or malformed DICOM file"),
        )
    return _result("magic_byte_structure", True, "Valid DICOM structure and signature")


def check_required_tags(metadata: dict) -> dict:
    """Check 2: Are the essential DICOM tags present and non-empty?"""
    missing = [
        tag for tag in REQUIRED_TAGS
        if metadata.get(tag) is None
        or str(metadata.get(tag)).strip() in ("", "None")
    ]
    if missing:
        return _result("required_tags", False, f"Missing or empty required tags: {', '.join(missing)}")
    return _result("required_tags", True, "All required tags present")


def check_uid_format(metadata: dict) -> dict:
    """Check 3: Does SOPInstanceUID follow valid DICOM UID format?"""
    uid = metadata.get("sop_instance_uid", "")
    if not uid or uid == "None":
        return _result("uid_format", False, "SOPInstanceUID is missing")
    if not re.match(r'^[0-9]+(\.[0-9]+)*$', uid):
        return _result("uid_format", False, f"SOPInstanceUID has invalid format: {uid}")
    if len(uid) > 64:
        return _result("uid_format", False, "SOPInstanceUID exceeds maximum length (64 characters)")
    return _result("uid_format", True, "SOPInstanceUID format is valid")


def check_study_date(metadata: dict) -> dict:
    """Check 4: Is the StudyDate realistic (not future, not absurdly old)?"""
    study_date_str = metadata.get("study_date", "")
    if not study_date_str or study_date_str == "None":
        return _result("timestamp_validity", True, "No StudyDate present (skipped)")

    try:
        study_date = datetime.strptime(study_date_str, "%Y%m%d")
    except ValueError:
        return _result("timestamp_validity", False, f"StudyDate has invalid format: {study_date_str}")

    today = datetime.now()
    earliest_reasonable = datetime(1990, 1, 1)

    if study_date > today:
        return _result("timestamp_validity", False, f"StudyDate is in the future: {study_date_str}")
    if study_date < earliest_reasonable:
        return _result("timestamp_validity", False, f"StudyDate is unrealistically old: {study_date_str}")

    return _result("timestamp_validity", True, "StudyDate is within a realistic range")


def check_pixel_data_consistency(metadata: dict) -> dict:
    """Check 6: Does PixelData size match Rows × Columns × BitsAllocated × SamplesPerPixel?"""
    if metadata.get("is_compressed", False):
        return _result(
            "pixel_data_consistency", True,
            "Compressed transfer syntax — raw pixel size check skipped",
        )

    rows           = metadata.get("rows")
    columns        = metadata.get("columns")
    bits_allocated = metadata.get("bits_allocated")
    samples        = metadata.get("samples_per_pixel")
    actual_length  = metadata.get("pixel_data_length", 0)

    if not all([rows, columns, bits_allocated, samples]):
        return _result(
            "pixel_data_consistency", True,
            "Insufficient metadata to verify pixel data size (skipped)",
        )

    expected = int(rows * columns * (bits_allocated / 8) * samples)
    if abs(actual_length - expected) > 2:   # 2-byte DICOM even-padding tolerance
        return _result(
            "pixel_data_consistency", False,
            f"PixelData size mismatch: expected ~{expected} bytes, found {actual_length} bytes",
        )

    return _result("pixel_data_consistency", True, "PixelData size matches expected dimensions")


INJECTION_PATTERNS = [
    r"(?i)\bor\s+1\s*=\s*1\b",
    r"(?i)\bunion\s+select\b",
    r"(?i)\bdrop\s+table\b",
    r"(?i)<script.*?>",
    r"(?i)javascript:",
    r"(?i)\.\./",
    r"(?i)--\s*$",
    r"(?i);\s*(drop|delete|update|insert)\s",
]

INJECTION_TEXT_FIELDS = [
    "study_description",
    "manufacturer",
    "patient_name",
    "referring_physician",
    "institution_name",
]


def check_injection_patterns(metadata: dict) -> dict:
    """Check 7: Do any text metadata fields contain injection-style patterns?"""
    findings = []
    for field in INJECTION_TEXT_FIELDS:
        value = str(metadata.get(field, "") or "")
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, value):
                findings.append(f"{field}: matched ({pattern})")

    if findings:
        return _result("injection_patterns", False, "; ".join(findings))
    return _result("injection_patterns", True, "No injection patterns detected in text metadata")


def check_path_traversal(filename: str) -> dict:
    """Check 8: Does the filename contain path traversal or suspicious path patterns?"""
    suspicious = [
        r"\.\.[/\\]",
        r"^[/\\]",
        r"^[a-zA-Z]:[/\\]",
        r"%2e%2e",
        r"%00",
    ]
    for pattern in suspicious:
        if re.search(pattern, filename, re.IGNORECASE):
            return _result("path_traversal", False, f"Filename contains suspicious path pattern: {filename}")
    return _result("path_traversal", True, "Filename is safe")


MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


def check_file_size(file_size: int) -> dict:
    """Check 9: Is the file size within the allowed limit?"""
    if file_size > MAX_FILE_SIZE_BYTES:
        return _result(
            "file_size_limit", False,
            f"File size ({file_size} bytes) exceeds maximum ({MAX_FILE_SIZE_BYTES} bytes)",
        )
    return _result("file_size_limit", True, "File size within acceptable range")


def run_structural_checks(metadata: dict, filename: str = "", file_size: int = 0) -> list:
    results = [
        check_magic_byte_and_structure(metadata),
        check_path_traversal(filename),
        check_file_size(file_size),
    ]
    if metadata.get("is_valid_dicom", False):
        results.append(check_required_tags(metadata))
        results.append(check_uid_format(metadata))
        results.append(check_study_date(metadata))
        results.append(check_pixel_data_consistency(metadata))
        results.append(check_injection_patterns(metadata))
    return results