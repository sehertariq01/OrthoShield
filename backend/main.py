import os
import shutil
import stat
import hashlib
from pathlib import Path
from scanners.malware_scan import scan_file_for_malware
from scanners.yara_scan import scan_file_with_yara
from scanners.dicom_parser import parse_dicom_metadata
from scanners.rule_checks import (
    check_magic_byte_and_structure,
    check_path_traversal,
    check_file_size,
    check_required_tags,
    check_uid_format,
    check_study_date,
    check_pixel_data_consistency,
    check_injection_patterns,
)

from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File, Query
from sqlalchemy.orm import Session
from scanners.ml_anomaly import check_ml_anomaly
from scanners.virustotal_scan import check_virustotal
from scanners.embedded_extractor import check_embedded_objects
from scanners.scoring_engine import calculate_risk_score
from scanners.orthanc_client import forward_to_orthanc
from database import Base, engine, get_db

from utils.encryption import encrypt_value
import models
from schemas import (
    UserCreate,
    UserLogin,
    Token,
    UploadResponse,
    AlertUpdateSchema,
    AuditVerifyResponse,
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_role,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_audit_log(db: Session, event: str, username: str, details: str) -> None:
    """
    Append a tamper-evident entry to the audit log.
    Each row hashes (event + username + details + previous_hash) so that
    any retrospective modification of the chain is detectable.
    """
    last = (
        db.query(models.AuditLog)
        .order_by(models.AuditLog.id.desc())
        .first()
    )
    previous_hash = last.current_hash if last else ""
    content = f"{event}|{username}|{details}|{previous_hash}"
    current_hash = hashlib.sha256(content.encode()).hexdigest()

    entry = models.AuditLog(
        event=event,
        username=username,
        details=details,
        previous_hash=previous_hash,
        current_hash=current_hash,
    )
    db.add(entry)
    db.commit()


def check_replay(metadata: dict, file_hash: str, db: Session) -> dict:
    """
    Fix 5 — Check 9: Distinguish benign resends from tamper/replay attacks.

    Hospitals resend identical studies constantly — retries, PACS routing
    loops, network drops.  Identical hash is a *dedupe* event, not a threat.
    The genuine attack signal is the same SOPInstanceUID arriving with
    *different* bytes: the content was altered between submissions.

    Hash match    → passed=True, is_duplicate=True, skipped=True
                    (no score contribution — benign resend)
    UID conflict  → passed=False, is_duplicate=False
                    (scored as replay_detection failure, weight 15)
    New file      → passed=True, is_duplicate=False
    """
    # ── Exact hash match — benign resend, do not penalise ────────────────────
    existing_hash = db.query(models.SHA256Store).filter(
        models.SHA256Store.file_hash == file_hash
    ).first()

    if existing_hash:
        return {
            "name":              "replay_detection",
            "passed":            True,
            "scanner_available": True,
            "skipped":           True,          # excluded from denominator
            "is_duplicate":      True,
            "detail": (
                f"Identical file previously scanned "
                f"(scan_log id={existing_hash.id if hasattr(existing_hash, 'id') else '?'}) "
                f"— benign resend, not scored"
            ),
        }

    # ── Same SOPInstanceUID, different bytes — tamper or replay ──────────────
    sop_uid = metadata.get("sop_instance_uid")
    if sop_uid and sop_uid != "None":
        conflict = db.query(models.SHA256Store).filter(
            models.SHA256Store.sop_instance_uid == sop_uid,
            models.SHA256Store.file_hash        != file_hash,
        ).first()

        if conflict:
            return {
                "name":              "replay_detection",
                "passed":            False,
                "scanner_available": True,
                "skipped":           False,
                "is_duplicate":      False,
                "detail": (
                    f"SOPInstanceUID {sop_uid} already recorded under a "
                    f"different hash — content differs from the original study "
                    f"(possible tamper or replay attack)"
                ),
            }

    # ── New file ──────────────────────────────────────────────────────────────
    return {
        "name":              "replay_detection",
        "passed":            True,
        "scanner_available": True,
        "skipped":           False,
        "is_duplicate":      False,
        "detail":            "No prior record of this file or SOPInstanceUID",
    }



# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OrthoShield",
    description="Secure DICOM Medical Imaging Security Platform",
    version="1.0.0",
)
# Fix 1: registered below after MaxBodySizeMiddleware class is defined
# (class definition cannot reference `app` before `app` exists, and
#  `app` cannot reference the class before the class is defined; we
#  use app.add_middleware after both exist — see after QUARANTINE_DIR setup)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Fix 1: Enforce upload size limit at the ASGI layer
# ---------------------------------------------------------------------------
# 100 MB hard ceiling.  Must match (or be smaller than) any value in
# check_file_size() in rule_checks.py.
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024   # 100 MB hard ceiling


class MaxBodySizeMiddleware:
    """
    Raw ASGI middleware that enforces a request body size limit without
    buffering the entire body into memory first.

    Why not BaseHTTPMiddleware?
    BaseHTTPMiddleware buffers the complete body before calling dispatch(),
    so a streaming gate inside dispatch() would still cause full buffering.
    A raw ASGI middleware wraps the ASGI `receive` callable directly:

      - Content-Length shortcut (Stage 1): if the client declares a size
        that already exceeds the limit, return 413 immediately before the
        first byte is received.
      - Streaming gate (Stage 2): wrap `receive` in a counter; as each
        http.request chunk arrives, add its length to a running total and
        short-circuit with 413 the moment the total exceeds the limit.
        Application code (file.file.read) only ever sees data that has
        already passed the gate.
    """

    def __init__(self, app):
        self._app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return

        # Stage 1 — Content-Length shortcut
        headers = dict(scope.get("headers", []))
        cl_raw = headers.get(b"content-length", b"")
        try:
            if cl_raw and int(cl_raw) > MAX_FILE_SIZE_BYTES:
                await self._send_413(send)
                return
        except ValueError:
            pass

        # Stage 2 — wrap receive with a streaming byte counter
        total_received = 0
        limit_exceeded = False

        async def counted_receive():
            nonlocal total_received, limit_exceeded
            message = await receive()
            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                total_received += len(chunk)
                if total_received > MAX_FILE_SIZE_BYTES:
                    limit_exceeded = True
                    # Return a terminal empty body so the app doesn't hang
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        # We need to check limit_exceeded between sending the request and
        # responding.  We do this by wrapping `send` to intercept the first
        # response event: if the limit was exceeded by then, swap it for 413.
        first_response_sent = False

        async def guarded_send(message):
            nonlocal first_response_sent
            if limit_exceeded and not first_response_sent and message["type"] == "http.response.start":
                first_response_sent = True
                await self._send_413(send)
                return
            first_response_sent = True
            await send(message)

        await self._app(scope, counted_receive, guarded_send)

        # If the limit was hit but the app didn't attempt to send a response
        # (e.g., exception raised), send 413 now.
        if limit_exceeded and not first_response_sent:
            await self._send_413(send)

    @staticmethod
    async def _send_413(send):
        body = (
            f"Request body too large. "
            f"Maximum allowed: {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
        ).encode()
        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"text/plain"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})


# Register after both `app` and the class exist
app.add_middleware(MaxBodySizeMiddleware)


# Fix 3: Quarantine directory — blocked files are moved here instead of deleted.
# Evidence is preserved for incident investigation. Files are stored read-only,
# named by hash so they cannot collide or be re-executed by extension.
QUARANTINE_DIR = Path(__file__).parent / "quarantine"
QUARANTINE_DIR.mkdir(exist_ok=True)


def _set_readonly(path: str) -> None:
    """
    Set a file to read-only in a cross-platform way.

    os.chmod with stat.S_IRUSR is a POSIX permission model; on Windows it
    only clears the write bit in the ACL for the owner via the CRT layer —
    it does NOT set FILE_ATTRIBUTE_READONLY and is therefore not enforced by
    the Windows filesystem (Explorer, CMD, and most Win32 apps ignore it).

    This function uses the Win32 SetFileAttributesW call via ctypes when
    running on Windows, and falls back to the POSIX chmod on other platforms.
    """
    if os.name == "nt":
        import ctypes
        FILE_ATTRIBUTE_READONLY = 0x01
        # GetFileAttributesW first so we don't clobber other attribute flags
        attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
        if attrs == 0xFFFFFFFF:
            attrs = 0  # INVALID_FILE_ATTRIBUTES — start fresh
        ctypes.windll.kernel32.SetFileAttributesW(path, attrs | FILE_ATTRIBUTE_READONLY)
    else:
        # POSIX: owner read-only, no write or execute for anyone
        os.chmod(path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def quarantine_file(file_path: str, file_hash: str) -> str:
    """
    Move a blocked file to isolated storage, named by hash, then set read-only.
    Returns the destination path string for logging.
    """
    dest = QUARANTINE_DIR / f"{file_hash}.quarantine"
    try:
        shutil.move(file_path, str(dest))
        _set_readonly(str(dest))
    except Exception as e:
        print(f"[WARN] Could not quarantine '{file_path}': {e}")
    return str(dest)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "OrthoShield Backend Running",
        "status": "success",
    }


@app.post("/users")
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_role(["admin"])),  # admin-only
):
    """Create a new user account. Requires an existing admin JWT."""
    existing = db.query(models.User).filter(
        models.User.username == user.username
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{user.username}' is already taken",
        )

    new_user = models.User(
        username=user.username,
        password_hash=hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    write_audit_log(
        db,
        event="USER_CREATED",
        username=current_admin["username"],
        details=f"Created user '{new_user.username}' with role '{new_user.role}'",
    )

    return {
        "message": "User created successfully",
        "user_id": new_user.id,
        "username": new_user.username,
        "role": new_user.role,
    }


@app.post("/login", response_model=Token)
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == credentials.username
    ).first()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    user.ip_address = encrypt_value(request.client.host)
    db.commit()

    token = create_access_token(username=user.username, role=user.role)

    write_audit_log(
        db,
        event="LOGIN",
        username=user.username,
        details=f"Successful login from {request.client.host}",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
    }


@app.post("/logout")
def logout(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invalidate the current JWT by adding its jti to the token blacklist.
    After calling this endpoint the token will be rejected by all protected routes.
    """
    jti = current_user.get("jti")
    if jti:
        blacklist_entry = models.TokenBlacklist(
            token_jti=jti,
            reason="User-initiated logout",
        )
        db.add(blacklist_entry)
        db.commit()

    write_audit_log(
        db,
        event="LOGOUT",
        username=current_user["username"],
        details="User logged out and token revoked",
    )

    return {"message": "Logged out successfully. Token has been revoked."}


@app.get("/me")
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user


@app.post("/upload", response_model=None)
def upload_dicom(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    file_content = file.file.read()
    file_hash = hashlib.sha256(file_content).hexdigest()

    # Run path traversal check FIRST, on the original filename, before touching the filesystem
    path_check = check_path_traversal(file.filename)

    # Always save using a sanitized filename (never trust the original path)
    safe_filename = os.path.basename(file.filename).replace("..", "")
    if not safe_filename:
        safe_filename = f"unnamed_{file_hash[:8]}.dcm"

    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(file_content)

    metadata = parse_dicom_metadata(file_path)

    rule_check_results = [
        check_magic_byte_and_structure(metadata),
        path_check,
        check_file_size(len(file_content)),
    ]

    if metadata.get("is_valid_dicom", False):
        rule_check_results.append(check_required_tags(metadata))
        rule_check_results.append(check_uid_format(metadata))
        rule_check_results.append(check_study_date(metadata))
        rule_check_results.append(check_pixel_data_consistency(metadata))
        rule_check_results.append(check_injection_patterns(metadata))

    malware_result = scan_file_for_malware(file_path)
    rule_check_results.append(malware_result)

    replay_result = check_replay(metadata, file_hash, db)
    rule_check_results.append(replay_result)

    yara_result = scan_file_with_yara(file_path)
    rule_check_results.append(yara_result)

    ml_result = check_ml_anomaly(file_path, metadata)
    rule_check_results.append(ml_result)

    # --- STATIC REPUTATION LOOKUP ----------------------------------------
    # Check 13: VirusTotal hash-only lookup (Fix 1: no file upload — PHI protection)
    vt_result = check_virustotal(file_hash)
    rule_check_results.append(vt_result)

    # Check 14: Embedded content extraction (static byte scan)
    # Pass metadata so the extractor can scope archive-sig scanning to the
    # non-PixelData region for compressed transfer syntaxes (Fix: J2K / RLE FP)
    embedded_result = check_embedded_objects(file_path, metadata)
    rule_check_results.append(embedded_result)
    # --------------------------------------------------------------------------

    # Store baseline hash for valid, genuinely new files.
    # Fix 5: only store baseline when file is genuinely new AND passed replay check
    # (a tamper collision has passed=False and must never be stored as a baseline).
    is_new_valid = (
        metadata.get("is_valid_dicom", False)
        and replay_result.get("passed", True)
        and not replay_result.get("is_duplicate", False)
    )
    if is_new_valid:

        existing = db.query(models.SHA256Store).filter(
            models.SHA256Store.file_hash == file_hash
        ).first()

        if not existing:
            new_baseline = models.SHA256Store(
                file_hash=file_hash,
                sop_instance_uid=metadata.get("sop_instance_uid"),
            )
            db.add(new_baseline)
            db.commit()


    scoring_result = calculate_risk_score(rule_check_results)

    # Persist scan result (Fix 2+3: store incomplete_scan and quarantine_path)
    new_scan_log = models.ScanLog(
        file_hash=file_hash,
        filename=file.filename,
        risk_score=scoring_result["risk_score"],
        decision=scoring_result["decision"],
        findings=str(scoring_result["failed_checks"]),
        uploaded_by=current_user["username"],
        incomplete_scan=scoring_result.get("incomplete_scan", False),
    )
    db.add(new_scan_log)
    db.commit()
    db.refresh(new_scan_log)

    if scoring_result["decision"] == "BLOCKED":
        # Create per-check alerts (use new key names: name, detail)
        for failed_check in scoring_result["failed_checks"]:
            severity = (
                "CRITICAL" if failed_check["weight"] >= 20
                else ("HIGH" if failed_check["weight"] >= 10 else "MEDIUM")
            )
            new_alert = models.Alert(
                severity=severity,
                status="OPEN",
                source=failed_check["name"],       # was "check"
                finding=failed_check["detail"],     # was "reason"
                scan_log_id=new_scan_log.id,
            )
            db.add(new_alert)
        db.commit()

        # Fix 3: Quarantine instead of delete — preserve evidence
        quarantine_path = quarantine_file(file_path, file_hash)
        new_scan_log.quarantine_path = quarantine_path
        db.commit()

        write_audit_log(
            db,
            event="UPLOAD_BLOCKED",
            username=current_user["username"],
            details=(
                f"File '{file.filename}' blocked. "
                f"Risk score: {scoring_result['risk_score']}. "
                f"Reason: {scoring_result.get('reason', '')}. "
                f"Quarantined to: {quarantine_path}. "
                f"Incomplete scan: {scoring_result.get('incomplete_scan', False)}"
            ),
        )
    else:
        # File is clean — forward to Orthanc PACS
        orthanc_res = forward_to_orthanc(file_path)

        if orthanc_res.get("success"):
            # PACS has the file now — remove transient file from uploads/
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"[WARN] Could not remove uploaded file '{file_path}': {e}")

            write_audit_log(
                db,
                event="UPLOAD_CLEAN",
                username=current_user["username"],
                details=(
                    f"File '{file.filename}' accepted and forwarded to Orthanc. "
                    f"Instance ID: {orthanc_res.get('instance_id')}. "
                    f"Risk score: {scoring_result['risk_score']}."
                ),
            )
        else:
            # Orthanc failed (connection down, duplicate, or error) — retain file for retry
            print(f"[WARN] Orthanc forwarding failed for '{file.filename}': {orthanc_res.get('detail')}")
            write_audit_log(
                db,
                event="UPLOAD_CLEAN_FORWARD_FAILED",
                username=current_user["username"],
                details=(
                    f"File '{file.filename}' accepted (Risk score: {scoring_result['risk_score']}) "
                    f"but Orthanc forward failed: {orthanc_res.get('detail')}. "
                    f"Retaining in uploads/ for retry."
                ),
            )


    # ── Fix 2: Role-based PHI field filtering ────────────────────────────────
    # patient_name, referring_physician, and institution_name are PHI.
    # Only admin and analyst roles receive real values; viewer gets [REDACTED].
    # This applies to the API response only — the fields are never stored in
    # scan_logs, so there is no DB-level change required.
    PHI_FIELDS = ("patient_name", "referring_physician", "institution_name")
    role = current_user.get("role", "viewer")
    if role not in ("admin", "analyst"):
        metadata_out = dict(metadata)
        for field in PHI_FIELDS:
            if field in metadata_out:
                metadata_out[field] = "[REDACTED]"
    else:
        metadata_out = metadata

    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "file_hash": file_hash,
        "file_size": len(file_content),
        "metadata": metadata_out,
        "rule_checks": rule_check_results,
        "risk_score": scoring_result["risk_score"],
        "decision": scoring_result["decision"],
        "incomplete_scan": scoring_result.get("incomplete_scan", False),
        "unavailable_engines": scoring_result.get("unavailable_engines", []),
        "failed_checks_summary": scoring_result["failed_checks"],
    }


# ---------------------------------------------------------------------------
# SOC Monitoring & Management Endpoints (Fix 16 & 17)
# ---------------------------------------------------------------------------

@app.get("/scans")
def list_scans(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    decision: str | None = None,
    current_user: dict = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db),
):
    """
    List scan logs with pagination and optional decision filter.
    Role-gated: admin and analyst only (viewers receive 403 Forbidden).
    """
    query = db.query(models.ScanLog)
    if decision:
        query = query.filter(models.ScanLog.decision == decision.upper())

    total = query.count()
    scans = query.order_by(models.ScanLog.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "scans": [
            {
                "id": s.id,
                "file_hash": s.file_hash,
                "filename": s.filename,
                "risk_score": s.risk_score,
                "decision": s.decision,
                "uploaded_by": s.uploaded_by,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "quarantine_path": s.quarantine_path,
                "incomplete_scan": s.incomplete_scan,
                "findings": s.findings,
            }
            for s in scans
        ],
    }


@app.get("/alerts")
def list_alerts(
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    status: str | None = "OPEN",
    severity: str | None = None,
    current_user: dict = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db),
):
    """
    List security alerts with status and severity filters.
    Role-gated: admin and analyst only.
    """
    query = db.query(models.Alert)

    if status and status.upper() != "ALL":
        query = query.filter(models.Alert.status == status.upper())

    if severity and severity.upper() != "ALL":
        query = query.filter(models.Alert.severity == severity.upper())

    total = query.count()
    alerts = query.order_by(models.Alert.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "alerts": [
            {
                "id": a.id,
                "severity": a.severity,
                "status": a.status,
                "source": a.source,
                "finding": a.finding,
                "scan_log_id": a.scan_log_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            }
            for a in alerts
        ],
    }


@app.patch("/alerts/{alert_id}")
def update_alert_status(
    alert_id: int,
    payload: AlertUpdateSchema,
    current_user: dict = Depends(require_role(["admin", "analyst"])),
    db: Session = Depends(get_db),
):
    """
    Triage and update alert status (e.g. OPEN -> RESOLVED / IGNORED).
    Role-gated: admin and analyst only.
    """
    new_status = payload.status.upper()
    if new_status not in ("OPEN", "RESOLVED", "IGNORED"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid alert status '{payload.status}'. Must be OPEN, RESOLVED, or IGNORED.",
        )

    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {alert_id} not found",
        )

    old_status = alert.status
    alert.status = new_status
    alert.resolved_at = datetime.now(timezone.utc) if new_status in ("RESOLVED", "IGNORED") else None

    db.commit()
    db.refresh(alert)

    write_audit_log(
        db,
        event="ALERT_UPDATED",
        username=current_user["username"],
        details=f"Alert {alert_id} status changed from {old_status} to {new_status}",
    )

    return {
        "message": f"Alert {alert_id} updated successfully",
        "alert": {
            "id": alert.id,
            "severity": alert.severity,
            "status": alert.status,
            "source": alert.source,
            "finding": alert.finding,
            "scan_log_id": alert.scan_log_id,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        },
    }


@app.get("/audit/verify", response_model=AuditVerifyResponse)
def verify_audit_ledger_chain(
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Walk the tamper-evident audit log SHA-256 hash chain from genesis to head.
    Detects any retrospective deletion, insertion, or attribute tampering.
    Role-gated: admin only.
    """
    logs = db.query(models.AuditLog).order_by(models.AuditLog.id.asc()).all()

    expected_previous = ""
    for log in logs:
        # Step 1: Verify link to previous row
        if log.previous_hash != expected_previous:
            return {
                "valid": False,
                "broken_at_id": log.id,
                "entries_verified": log.id - 1 if log.id else 0,
                "detail": (
                    f"Chain link broken at entry ID {log.id}: "
                    f"previous_hash mismatch (expected '{expected_previous}', found '{log.previous_hash}')"
                ),
            }

        # Step 2: Recalculate row's SHA-256 digest
        content = f"{log.event}|{log.username}|{log.details}|{log.previous_hash}"
        expected_current = hashlib.sha256(content.encode()).hexdigest()

        if log.current_hash != expected_current:
            return {
                "valid": False,
                "broken_at_id": log.id,
                "entries_verified": log.id - 1 if log.id else 0,
                "detail": (
                    f"Chain integrity failure at entry ID {log.id}: "
                    f"content tampered (recalculated '{expected_current}', found '{log.current_hash}')"
                ),
            }

        expected_previous = log.current_hash

    return {
        "valid": True,
        "entries_verified": len(logs),
        "broken_at_id": None,
        "detail": f"Audit ledger chain is cryptographically intact across all {len(logs)} entries.",
    }