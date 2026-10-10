"""
Check 14 (Static): Scan raw DICOM bytes for dangerous embedded content.

Fix: compressed pixel data (J2K, JPEG-LL, RLE) was triggering false
positives on archive signatures (GZIP in particular) because the compressed
pixel bytes coincidentally match the two-byte GZIP magic (0x1f 0x8b) and
similar short sequences.

Scanning strategy
─────────────────
Two scanning regions:

  full_bytes   — entire file, always.
                 Used for: MZ (PE), ELF — executables have no legitimate
                 place anywhere in a DICOM file, even inside pixel data.

  header_bytes — [DICOM_HEADER_OFFSET : pixel_data_start] when the file
                 uses a compressed transfer syntax; full_bytes otherwise.
                 Used for: archive signatures (ZIP, GZIP, 7z, RAR, Java),
                 PDF, and runtime script patterns.

pixel_data_start is estimated as:
  len(raw_bytes) - pixel_data_length    (when pixel_data_length is known)

This is correct for single-frame files (PixelData is the last element) and
a safe approximation for multi-frame; it may include a few bytes of
sequence overhead, which does not affect correctness — those bytes won't
contain archive magic either.

If pixel_data_length is 0 or absent, archive scan covers the full file
(same as before for uncompressed).
"""
import os
import re

# ---------------------------------------------------------------------------
# Signatures — executables: flagged in the ENTIRE file (including pixel data)
# ---------------------------------------------------------------------------
EXECUTABLE_SIGNATURES = [
    (b"MZ",      "Windows PE Executable (.exe / .dll)"),
    (b"\x7fELF", "Linux ELF Executable"),
]

# ---------------------------------------------------------------------------
# Signatures — archives / documents: only flagged OUTSIDE pixel data for
# compressed transfer syntaxes (avoids false positives on J2K, JPEG-LL, RLE)
# ---------------------------------------------------------------------------
ARCHIVE_SIGNATURES = [
    (b"PK\x03\x04",         "ZIP Archive (may contain malware)"),
    (b"%PDF",                "Embedded PDF (may contain JavaScript/macros)"),
    (b"\xca\xfe\xba\xbe",   "Java Class File"),
    (b"Rar!\x1a\x07",       "RAR Archive"),
    (b"\x1f\x8b",           "GZIP Archive"),
    (b"7z\xbc\xaf\x27\x1c", "7-Zip Archive"),
]

# ---------------------------------------------------------------------------
# Runtime / script patterns: scanned in header_bytes region (text patterns
# will not appear in compressed binary pixel data, so no real restriction)
# ---------------------------------------------------------------------------
RUNTIME_PATTERNS = [
    (rb"<script[\s>]",      "HTML/JavaScript <script> tag"),
    (rb"javascript\s*:",    "JavaScript protocol handler"),
    (rb"eval\s*\(",         "JavaScript eval() call"),
    (rb"exec\s*\(",         "Shell/Python exec() call"),
    (rb"/bin/bash",         "Bash shell reference"),
    (rb"/bin/sh",           "Unix shell reference"),
    (rb"cmd\.exe",          "Windows CMD.exe reference"),
    (rb"powershell",        "PowerShell reference"),
    (rb"WScript\.Shell",    "Windows Script Host"),
    (rb"CreateObject\s*\(", "COM/ActiveX object creation"),
    (rb"ActiveXObject",     "ActiveX instantiation"),
    (rb"document\.write",   "JavaScript DOM write"),
    (rb"XMLHttpRequest",    "JavaScript HTTP request"),
]

# ---------------------------------------------------------------------------
# Suspicious DICOM private/encapsulated-document tags (header presence only)
# ---------------------------------------------------------------------------
SUSPICIOUS_DICOM_TAGS = [
    (b"\x42\x00\x11\x00", "(0042,0011) Encapsulated Document"),
    (b"\x42\x00\x12\x00", "(0042,0012) MIME Type of Encapsulated Document"),
    (b"\x08\x00\x6e\x00", "(0008,006E) Referenced Series Sequence (unusual)"),
]

# Skip the 128-byte preamble + 4-byte "DICM" magic when searching signatures
DICOM_HEADER_OFFSET = 132


def check_embedded_objects(file_path: str, metadata: dict | None = None) -> dict:
    """
    Check 14 (Static): Scan raw DICOM bytes for dangerous embedded content.

    Parameters
    ----------
    file_path : str
        Path to the file on disk.
    metadata : dict, optional
        Parsed DICOM metadata dict.  Provides `is_compressed` and
        `pixel_data_length` so archive-signature scanning can be limited
        to the non-PixelData region for compressed files.
    """
    result = {
        "name":              "embedded_objects",
        "passed":            True,
        "scanner_available": True,
        "skipped":           False,
        "detail":            "",
    }

    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read()

        # ── Determine archive-safe scan region ───────────────────────────────
        is_compressed    = bool(metadata and metadata.get("is_compressed", False))
        pixel_data_len   = int(metadata.get("pixel_data_length", 0)) if metadata else 0

        if is_compressed and pixel_data_len > 0:
            # Approximate pixel data start; PixelData is the last DICOM element.
            pixel_data_start = max(DICOM_HEADER_OFFSET,
                                   len(raw_bytes) - pixel_data_len)
            header_bytes = raw_bytes[:pixel_data_start]
        else:
            # Uncompressed or no pixel data info → scan entire file
            header_bytes = raw_bytes

        full_bytes = raw_bytes   # executable scan always covers everything

        findings = []

        # Sub-check A: Executable signatures — scan ENTIRE file
        for sig, desc in EXECUTABLE_SIGNATURES:
            pos = full_bytes.find(sig, DICOM_HEADER_OFFSET)
            if pos != -1:
                findings.append(f"Embedded {desc} at byte offset {pos}")

        # Sub-check B: Archive/doc signatures — scan NON-PixelData region
        for sig, desc in ARCHIVE_SIGNATURES:
            pos = header_bytes.find(sig, DICOM_HEADER_OFFSET)
            if pos != -1:
                findings.append(f"Embedded {desc} at byte offset {pos}")

        # Sub-check C: Runtime / script patterns — scan non-PixelData region
        for pattern, desc in RUNTIME_PATTERNS:
            match = re.search(pattern, header_bytes, re.IGNORECASE)
            if match:
                findings.append(
                    f"Runtime pattern '{desc}' at offset {match.start()}"
                )

        # Sub-check D: Suspicious DICOM encapsulated-document tags (header)
        for tag_bytes, tag_desc in SUSPICIOUS_DICOM_TAGS:
            if tag_bytes in header_bytes:
                findings.append(f"Suspicious DICOM tag: {tag_desc}")

        if findings:
            result["passed"] = False
            scan_scope = "header" if (is_compressed and pixel_data_len > 0) else "full file"
            result["detail"] = (
                f"{len(findings)} dangerous item(s) "
                f"[archive scan scoped to {scan_scope}]: "
                + "; ".join(findings)
            )
        else:
            result["detail"] = "No dangerous embedded objects or runtime patterns found"

    except Exception as e:
        result["scanner_available"] = False
        result["detail"]            = f"Embedded object check error: {e}"

    return result
