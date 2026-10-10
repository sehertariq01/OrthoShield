# OrthoShield Technical Documentation

**System Version:** 1.0.0-beta | **Status:** Core Gateway, Dynamic Scoring & Orthanc Integration Complete  
**Date of Audit:** September 2026 | **Target Architecture:** Hospital SOC DICOM Security Gateway

---

## 1. Project Overview

OrthoShield is a high-assurance, pre-ingestion security gateway designed to sit directly in front of hospital Picture Archiving and Communication Systems (PACS), specifically Orthanc. In modern clinical environments, medical imaging pipelines frequently ingest DICOM files from untrusted external sources (referring clinics, teleradiology portals, USB media, and mobile modalities). Attackers and corrupted endpoints can exploit DICOM parser vulnerabilities, embed malicious executables or polyglot payloads within pixel data, tamper with patient tags, or launch path traversal and injection attacks. OrthoShield intercepts incoming DICOM uploads, subjects each file to a 14-stage static and analytical security pipeline, calculates a dynamic weighted risk score, isolates threats in a tamper-evident Windows read-only quarantine, and forwards verified clean instances directly into Orthanc via its REST API while maintaining a cryptographic SHA-256 audit ledger.

---

## 2. System Architecture

Below is the verified end-to-end flow of a DICOM upload through the OrthoShield gateway as implemented in [`backend/main.py`](file:///d:/OrthoShield/backend/main.py):

```
Client / Ingestion Endpoint
  │
  ├─► [1] Raw ASGI Middleware (MaxBodySizeMiddleware)
  │     ├── Stage 1: Content-Length header check (> 100 MB -> HTTP 413 immediately, 0 bytes read)
  │     └── Stage 2: Streaming byte counter (short-circuits at 100 MB -> HTTP 413)
  │
  ├─► [2] Path Traversal Pre-Screen (scanners/rule_checks.py: check_path_traversal)
  │     └── Evaluates raw file.filename before writing to disk; sanitizes filename
  │
  ├─► [3] Disk Buffering (backend/uploads/<safe_filename>)
  │     └── Computes SHA-256 file hash
  │
  ├─► [4] DICOM Header Parsing (scanners/dicom_parser.py: parse_dicom_metadata)
  │     └── Extracts UIDs, modality, pixel attributes, study date, transfer syntax
  │
  ├─► [5] Security Inspection Pipeline (14 Checks in Sequence)
  │     ├── Structural & Rules: magic_byte, required_tags, uid_format, study_date,
  │     │                       pixel_data_consistency, injection_patterns, file_size
  │     ├── Malware & Signatures: ClamAV (WSL socket), YARA rules (WSL subprocess)
  │     ├── Identity & Integrity: replay_detection (tamper vs benign dedupe in SHA256Store)
  │     ├── Statistical & ML: ml_anomaly_score (Isolation Forest + entropy Z-score)
  │     ├── Threat Intelligence: VirusTotal (hash-only privacy lookup, no PHI upload)
  │     └── Deep Content: embedded_objects (PE/ELF executable & compressed-scoped archive scans)
  │
  ├─► [6] Risk Scoring Engine (scanners/scoring_engine.py: calculate_risk_score)
  │     ├── Fail-Closed Check: If any scanner is offline -> BLOCKED (incomplete_scan=True)
  │     ├── Denominator: Sum of weights of checks that ran (excluding skipped=True)
  │     ├── Hard-Block Evaluation: magic_byte, malware, yara, VT, traversal, replay
  │     └── Threshold Comparison: risk_score >= BLOCK_THRESHOLD (15) -> BLOCKED
  │
  ├──► [DECISION: BLOCKED]
  │     ├── Moves file to backend/quarantine/<sha256>.quarantine
  │     ├── Sets Win32 FILE_ATTRIBUTE_READONLY (ctypes SetFileAttributesW)
  │     ├── Persists Alert records and ScanLog (incomplete_scan, quarantine_path)
  │     └── Appends UPLOAD_BLOCKED to cryptographic SHA-256 AuditLog chain
  │
  └──► [DECISION: CLEAN]
        ├── Forwards instance to Orthanc (scanners/orthanc_client.py: POST /instances)
        ├── SUCCESS: Removes transient file from backend/uploads/; logs UPLOAD_CLEAN
        ├── FAILURE: Retains file in uploads/ for retry; logs UPLOAD_CLEAN_FORWARD_FAILED
        ├── Records new baseline in sha256_store table (if not a duplicate)
        └── Role-based PHI Redaction: Replaces patient_name, physician, institution
            with "[REDACTED]" for viewer role; passes real metadata to admin/analyst.
```

---

## 3. Complete Module Inventory

Every Python module in `backend/` and `backend/scanners/` was inspected on disk:

### Backend Core (`backend/`)

| File Name | Purpose | Exposed Functions / Classes / Endpoints | Implementation Status |
|:---|:---|:---|:---:|
| [`main.py`](file:///d:/OrthoShield/backend/main.py) | Main FastAPI gateway application, ASGI body limiter, upload pipeline, and SOC routes | `MaxBodySizeMiddleware`, `quarantine_file()`, `write_audit_log()`, `check_replay()`, `GET /`, `POST /users`, `POST /login`, `POST /logout`, `GET /me`, `POST /upload`, `GET /scans`, `GET /alerts`, `PATCH /alerts/{id}`, `GET /audit/verify` | **COMPLETE** |
| [`auth.py`](file:///d:/OrthoShield/backend/auth.py) | Authentication, password hashing (passlib/bcrypt), JWT issuance and role-based gating | `hash_password()`, `verify_password()`, `create_access_token()`, `get_current_user()`, `require_role()` | **COMPLETE** |
| [`config.py`](file:///d:/OrthoShield/backend/config.py) | Environment configuration loader and secret validation | Exports `SECRET_KEY`, `ALGORITHM`, `TOKEN_EXPIRY`, `VT_API_KEY`, `ORTHANC_URL`, `ORTHANC_USERNAME`, `ORTHANC_PASSWORD` | **COMPLETE** |
| [`database.py`](file:///d:/OrthoShield/backend/database.py) | Database engine setup and session lifecycle manager for SQLite | `engine`, `SessionLocal`, `Base`, `get_db()` | **COMPLETE** |
| [`models.py`](file:///d:/OrthoShield/backend/models.py) | SQLAlchemy database ORM model definitions | `User`, `ScanLog`, `Alert`, `AuditLog`, `TokenBlacklist`, `SHA256Store` | **COMPLETE** |
| [`schemas.py`](file:///d:/OrthoShield/backend/schemas.py) | Pydantic v2 schemas for request validation and response formatting | `UserCreate`, `UserLogin`, `Token`, `UploadResponse`, `AlertUpdateSchema`, `AuditVerifyResponse` | **COMPLETE** |
| [`watcher.py`](file:///d:/OrthoShield/backend/watcher.py) | Continuous surveillance daemon polling Orthanc `/changes` feed | `handle_sigint()`, `fetch_instance_summary()`, `run_watcher()` | **COMPLETE** |
| [`custom_docs.py`](file:///d:/OrthoShield/backend/custom_docs.py) | Custom dark-themed Swagger UI documentation route | `setup_custom_docs(app)`, `GET /docs` | **COMPLETE** |
| [`data_retention_cleanup.py`](file:///d:/OrthoShield/backend/data_retention_cleanup.py) | Data retention policy enforcement script | `cleanup_old_logs(days=90)` | **COMPLETE** |
| [`diagnose_anomaly.py`](file:///d:/OrthoShield/backend/diagnose_anomaly.py) | Diagnostic utility for analyzing features of single DICOM files | `diagnose_file(file_path)` | **COMPLETE** |
| [`extract_features.py`](file:///d:/OrthoShield/backend/extract_features.py) | Batch feature extraction from training datasets to CSV | `calculate_file_entropy()`, `extract_features_from_file()`, `main()` | **COMPLETE** *(MR-only baseline)* |
| [`fetch_training_data.py`](file:///d:/OrthoShield/backend/fetch_training_data.py) | TCIA REST client for downloading mixed-modality DICOM series | `get_series()`, `download_series()`, `main()` | **COMPLETE** |
| [`generate_test_anomalies.py`](file:///d:/OrthoShield/backend/generate_test_anomalies.py) | Synthetic attack and corrupted DICOM generator for test suites | `create_anomalies()` | **COMPLETE** |
| [`test_isolation_forest.py`](file:///d:/OrthoShield/backend/test_isolation_forest.py) | CLI testing harness for Isolation Forest anomaly scores | `test_file(path)` | **COMPLETE** |
| [`train_isolation_forest.py`](file:///d:/OrthoShield/backend/train_isolation_forest.py) | Trains IsolationForest model and computes 5th-percentile threshold | `main()` | **COMPLETE** *(MR baseline)* |
| [`migrations/001_quarantine_columns.py`](file:///d:/OrthoShield/backend/migrations/001_quarantine_columns.py) | Idempotent SQLite migration for `quarantine_path` and `incomplete_scan` | `migrate()` | **COMPLETE** |
| [`tests/run_scoring_comparison.py`](file:///d:/OrthoShield/backend/tests/run_scoring_comparison.py) | Standalone scorer comparing old vs new denominator over 145 files | `old_score()`, `new_score()`, `run_comparison()` | **COMPLETE** |
| [`utils/encryption.py`](file:///d:/OrthoShield/backend/utils/encryption.py) | Fernet symmetric field-level encryption for sensitive DB fields | `encrypt_value()`, `decrypt_value()` | **COMPLETE** |

### Scanners Layer (`backend/scanners/`)

| File Name | Purpose | Exposed Functions | Implementation Status |
|:---|:---|:---|:---:|
| [`scanners/__init__.py`](file:///d:/OrthoShield/backend/scanners/__init__.py) | Package initializer | Empty | **COMPLETE** |
| [`scanners/dicom_parser.py`](file:///d:/OrthoShield/backend/scanners/dicom_parser.py) | Safe header parser and metadata dictionary builder using pydicom | `parse_dicom_metadata(file_path: str) -> dict` | **COMPLETE** |
| [`scanners/embedded_extractor.py`](file:///d:/OrthoShield/backend/scanners/embedded_extractor.py) | Deep static byte scanner for PE, ELF, scripts, and non-PixelData archives | `check_embedded_objects(file_path: str, metadata: dict = None) -> dict` | **COMPLETE** |
| [`scanners/malware_scan.py`](file:///d:/OrthoShield/backend/scanners/malware_scan.py) | Antivirus scanner connecting to ClamAV daemon over WSL socket | `windows_path_to_wsl()`, `scan_file_for_malware(file_path: str) -> dict` | **COMPLETE** |
| [`scanners/ml_anomaly.py`](file:///d:/OrthoShield/backend/scanners/ml_anomaly.py) | Unsupervised Isolation Forest and univariate entropy anomaly detector | `extract_features_for_inference()`, `check_ml_anomaly(file_path, metadata) -> dict` | **COMPLETE** |
| [`scanners/orthanc_client.py`](file:///d:/OrthoShield/backend/scanners/orthanc_client.py) | REST client for forwarding verified clean files to Orthanc `POST /instances` | `forward_to_orthanc(file_path: str) -> dict` | **COMPLETE** |
| [`scanners/rule_checks.py`](file:///d:/OrthoShield/backend/scanners/rule_checks.py) | 8 static structural, tag, date, size, and path validation checks | `check_magic_byte_and_structure()`, `check_required_tags()`, `check_uid_format()`, `check_study_date()`, `check_pixel_data_consistency()`, `check_injection_patterns()`, `check_file_size()`, `check_path_traversal()` | **COMPLETE** |
| [`scanners/scoring_engine.py`](file:///d:/OrthoShield/backend/scanners/scoring_engine.py) | Dynamic denominator weighted risk engine with hard-block evaluations | `calculate_risk_score(check_results: list) -> dict` | **COMPLETE** |
| [`scanners/virustotal_scan.py`](file:///d:/OrthoShield/backend/scanners/virustotal_scan.py) | Hash-only VirusTotal reputation lookup (privacy-preserving, no PHI upload) | `check_virustotal(file_hash: str) -> dict` | **COMPLETE** |
| [`scanners/yara_scan.py`](file:///d:/OrthoShield/backend/scanners/yara_scan.py) | Pattern matching signature scanner executing custom YARA rules in WSL | `windows_path_to_wsl()`, `scan_file_with_yara(file_path: str) -> dict` | **COMPLETE** |

---

## 4. The Security Check Pipeline

All 14 security checks defined in `CHECK_WEIGHTS` are listed below with their weights, hard-block classification, implementing function, and exact source file locations:

| # | Check Name (`CHECK_WEIGHTS` Key) | Weight | Hard Block? | Implementing Function | Source File & Line |
|:---:|:---|:---:|:---:|:---|:---|
| **1** | `magic_byte_structure` | 15 | **YES** | `check_magic_byte_and_structure(metadata)` | [`backend/scanners/rule_checks.py:23`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L23) |
| **2** | `path_traversal` | 10 | **YES** | `check_path_traversal(filename)` | [`backend/scanners/rule_checks.py:161`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L161) |
| **3** | `file_size_limit` | 5 | NO | `check_file_size(file_size)` | [`backend/scanners/rule_checks.py:145`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L145) |
| **4** | `required_tags` | 5 | NO | `check_required_tags(metadata)` | [`backend/scanners/rule_checks.py:33`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L33) |
| **5** | `uid_format` | 5 | NO | `check_uid_format(metadata)` | [`backend/scanners/rule_checks.py:45`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L45) |
| **6** | `timestamp_validity` | 5 | NO | `check_study_date(metadata)` | [`backend/scanners/rule_checks.py:57`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L57) |
| **7** | `pixel_data_consistency` | 5 | NO | `check_pixel_data_consistency(metadata)` | [`backend/scanners/rule_checks.py:87`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L87) |
| **8** | `injection_patterns` | 8 | NO | `check_injection_patterns(metadata)` | [`backend/scanners/rule_checks.py:118`](file:///d:/OrthoShield/backend/scanners/rule_checks.py#L118) |
| **9** | `malware_scan` | 30 | **YES** | `scan_file_for_malware(file_path)` | [`backend/scanners/malware_scan.py:30`](file:///d:/OrthoShield/backend/scanners/malware_scan.py#L30) |
| **10** | `replay_detection` | 15 | **YES** | `check_replay(metadata, file_hash, db)` | [`backend/main.py:69`](file:///d:/OrthoShield/backend/main.py#L69) |
| **11** | `yara_scan` | 20 | **YES** | `scan_file_with_yara(file_path)` | [`backend/scanners/yara_scan.py:33`](file:///d:/OrthoShield/backend/scanners/yara_scan.py#L33) |
| **12** | `ml_anomaly_score` | 15 | NO | `check_ml_anomaly(file_path, metadata)` | [`backend/scanners/ml_anomaly.py:68`](file:///d:/OrthoShield/backend/scanners/ml_anomaly.py#L68) |
| **13** | `virustotal` | 25 | **YES** | `check_virustotal(file_hash)` | [`backend/scanners/virustotal_scan.py:12`](file:///d:/OrthoShield/backend/scanners/virustotal_scan.py#L12) |
| **14** | `embedded_objects` | 20 | NO | `check_embedded_objects(file_path, metadata)` | [`backend/scanners/embedded_extractor.py:61`](file:///d:/OrthoShield/backend/scanners/embedded_extractor.py#L61) |

---

## 5. Scoring Engine Behavior

Directly quoted from [`backend/scanners/scoring_engine.py`](file:///d:/OrthoShield/backend/scanners/scoring_engine.py):

### 1. `HARD_BLOCK_CHECKS` Set Verbatim (Lines 50–57)
```python
HARD_BLOCK_CHECKS = {
    "magic_byte_structure",
    "malware_scan",
    "yara_scan",
    "virustotal",
    "path_traversal",        # Fix 4: promoted
    "replay_detection",      # Confirmed study tampering / UID collision
}
```

### 2. `BLOCK_THRESHOLD` Value (Line 74)
```python
BLOCK_THRESHOLD = 15   # provisional; re-tune post Fix 6
```

### 3. Dynamic Denominator Calculation Code (Lines 105–113, 133)
```python
    # skipped=True → no result, exclude from denominator AND from scoring
    ran = [
        c for c in check_results
        if c.get("scanner_available", True) and not c.get("skipped", False)
    ]

    # Fix 4: denominator is the sum of weights of checks that actually ran —
    # not the global constant sum of all possible check weights.
    denominator = sum(CHECK_WEIGHTS.get(c["name"], 5) for c in ran) or 1
    ...
    risk_score = round((risk_points / denominator) * 100, 2)
```

---

## 6. Database Schema

All 6 database tables defined in [`backend/models.py`](file:///d:/OrthoShield/backend/models.py) (SQLite backend: `orthoshield.db`):

### 1. `users`
| Column Name | Type | Nullable? | Constraints / Default |
|:---|:---|:---:|:---|
| `id` | `Integer` | No | Primary Key, Indexed |
| `username` | `String(100)` | No | Unique |
| `password_hash` | `String(255)` | No | Stored bcrypt hash |
| `role` | `String(20)` | Yes | Default: `"viewer"` (`admin`, `analyst`, `viewer`) |
| `ip_address` | `String(45)` | Yes | Fernet encrypted client IP |
| `is_active` | `Boolean` | Yes | Default: `True` |
| `created_at` | `DateTime(timezone=True)` | Yes | Server Default: `func.now()` |

### 2. `scan_logs`
| Column Name | Type | Nullable? | Constraints / Default |
|:---|:---|:---:|:---|
| `id` | `Integer` | No | Primary Key, Indexed |
| `file_hash` | `String(64)` | No | Indexed (SHA-256) |
| `filename` | `String(255)` | Yes | Uploaded file name |
| `risk_score` | `Float` | **Yes** | Nullable (None on incomplete scan) |
| `decision` | `String(20)` | Yes | `"CLEAN"` or `"BLOCKED"` |
| `findings` | `Text` | Yes | JSON string of check results / failures |
| `uploaded_by` | `String(100)` | Yes | Username of uploader |
| `created_at` | `DateTime(timezone=True)` | Yes | Server Default: `func.now()` |
| `quarantine_path` | `String(500)` | **Yes** | Absolute path if quarantined |
| `incomplete_scan` | `Boolean` | Yes | Default: `False` (True if engine offline) |

### 3. `alerts`
| Column Name | Type | Nullable? | Constraints / Default |
|:---|:---|:---:|:---|
| `id` | `Integer` | No | Primary Key, Indexed |
| `severity` | `String(20)` | Yes | `"LOW"`, `"MEDIUM"`, `"HIGH"`, `"CRITICAL"` |
| `status` | `String(20)` | Yes | Default: `"OPEN"` (`OPEN`, `RESOLVED`, `IGNORED`) |
| `source` | `String(50)` | Yes | e.g. `"malware_scan"`, `"yara_scan"`, `"rule_check"` |
| `finding` | `Text` | Yes | Human-readable alert finding |
| `scan_log_id` | `Integer` | Yes | Foreign reference to `scan_logs.id` |
| `created_at` | `DateTime(timezone=True)` | Yes | Server Default: `func.now()` |
| `resolved_at` | `DateTime(timezone=True)` | **Yes** | Timestamp of triage |

### 4. `audit_logs`
| Column Name | Type | Nullable? | Constraints / Default |
|:---|:---|:---:|:---|
| `id` | `Integer` | No | Primary Key, Indexed |
| `event` | `String(100)` | No | `LOGIN`, `LOGOUT`, `UPLOAD_CLEAN`, `UPLOAD_BLOCKED`, etc. |
| `username` | `String(100)` | Yes | Username triggering the action |
| `details` | `Text` | Yes | Action context and file details |
| `previous_hash` | `String(64)` | Yes | SHA-256 hash of previous row |
| `current_hash` | `String(64)` | No | Recalculated SHA-256 digest |
| `created_at` | `DateTime(timezone=True)` | Yes | Server Default: `func.now()` |

### 5. `token_blacklist`
| Column Name | Type | Nullable? | Constraints / Default |
|:---|:---|:---:|:---|
| `id` | `Integer` | No | Primary Key, Indexed |
| `token_jti` | `String(255)` | No | Unique JWT ID (`jti`) |
| `revoked_at` | `DateTime(timezone=True)` | Yes | Server Default: `func.now()` |
| `reason` | `String(100)` | Yes | e.g. `"User logout"` |

### 6. `sha256_store`
| Column Name | Type | Nullable? | Constraints / Default |
|:---|:---|:---:|:---|
| `id` | `Integer` | No | Primary Key, Indexed |
| `file_hash` | `String(64)` | No | Unique, Indexed |
| `sop_instance_uid` | `String(255)` | Yes | DICOM SOPInstanceUID for baseline replay check |
| `baseline_created_at` | `DateTime(timezone=True)` | Yes | Server Default: `func.now()` |

---

## 7. API Surface

All registered HTTP route endpoints across the application:

| HTTP Method | Route Path | Auth Dependency | Role Requirement | Description |
|:---:|:---|:---|:---|:---|
| `GET` | `/` | None | Public | Health and basic service status |
| `GET` | `/docs` | None | Public | Dark-themed interactive Swagger UI API documentation |
| `POST` | `/users` | `require_role(["admin"])` | `admin` | Create new system user account (min 10 chars password) |
| `POST` | `/login` | None | Public | Authenticate credentials and obtain signed JWT access token |
| `POST` | `/logout` | `get_current_user` | All authenticated | Revoke active JWT by registering its `jti` in `token_blacklist` |
| `GET` | `/me` | `get_current_user` | All authenticated | Return username and role payload of currently authenticated JWT |
| `POST` | `/upload` | `get_current_user` | All authenticated | Upload DICOM file, execute 14 security checks, forward/quarantine, and return results (PHI redacted for viewer) |
| `GET` | `/scans` | `require_role(["admin", "analyst"])` | `admin`, `analyst` | Query paginated scan logs with optional `decision` filtering |
| `GET` | `/alerts` | `require_role(["admin", "analyst"])` | `admin`, `analyst` | Query security alerts with `status` and `severity` filtering |
| `PATCH` | `/alerts/{alert_id}` | `require_role(["admin", "analyst"])` | `admin`, `analyst` | Triage alert status (`OPEN`, `RESOLVED`, `IGNORED`) and log audit event |
| `GET` | `/audit/verify` | `require_role(["admin"])` | `admin` | Cryptographically verify SHA-256 audit ledger hash chain from genesis to head |

---

## 8. Environment & Configuration

Environment variables read via `os.environ.get`:

| Variable Name | File & Line Where Read | Default Value | Purpose |
|:---|:---|:---|:---|
| `ORTHOSHIELD_SECRET_KEY` | [`backend/config.py:7`](file:///d:/OrthoShield/backend/config.py#L7) | `""` *(raises RuntimeError if empty)* | Secret HMAC key for signing JWT tokens |
| `VT_API_KEY` | [`backend/config.py:24`](file:///d:/OrthoShield/backend/config.py#L24) | `""` | VirusTotal v3 API key for hash lookups |
| `ORTHANC_URL` | [`backend/config.py:27`](file:///d:/OrthoShield/backend/config.py#L27) | `"http://localhost:9042"` | Base URL of target Orthanc PACS REST API |
| `ORTHANC_USERNAME` | [`backend/config.py:28`](file:///d:/OrthoShield/backend/config.py#L28) | `"orthanc"` | HTTP Basic Auth username for Orthanc |
| `ORTHANC_PASSWORD` | [`backend/config.py:29`](file:///d:/OrthoShield/backend/config.py#L29) | `"orthanc"` | HTTP Basic Auth password for Orthanc |
| `CLAMAV_HOST` | [`backend/scanners/malware_scan.py:13`](file:///d:/OrthoShield/backend/scanners/malware_scan.py#L13) | `"127.0.0.1"` | Host/IP of ClamAV daemon running in WSL |
| `CLAMAV_PORT` | [`backend/scanners/malware_scan.py:14`](file:///d:/OrthoShield/backend/scanners/malware_scan.py#L14) | `3310` | TCP port for ClamAV daemon network socket |

*Template configuration:* Available at [`backend/.env.example`](file:///d:/OrthoShield/backend/.env.example).

---

## 9. External Dependencies

### 1. Python Package Dependencies (`requirements.txt` & Environment)
```
fastapi==0.141.1
uvicorn==0.52.0
starlette==1.3.1
python-multipart==0.0.32
SQLAlchemy==2.0.51
pydantic==2.13.4
pydantic_core==2.46.4
pydicom==3.0.2
scikit-learn==1.9.0
scipy==1.18.0
numpy==2.5.1
pandas==3.0.5
joblib==1.5.3
python-jose==3.5.0
passlib==1.7.4
bcrypt==5.0.0
cryptography==50.0.0
pyClamd==0.4.0
requests==2.34.2
python-dotenv==1.2.2
```

### 2. External Non-Python Services & daemons
| Service | Runtime Platform | Host / Port Binding | Purpose |
|:---|:---|:---|:---|
| **Orthanc PACS** | Docker Container (`jodogne/orthanc-plugins`) | `127.0.0.1:9042` (mapped to internal `8042`) | Clinical PACS instance receiving clean DICOMs |
| **ClamAV (`clamd`)** | WSL2 Linux Distribution | `172.20.157.218:3310` (WSL IP) | Real-time antivirus signature scanning engine |
| **YARA (`yara` CLI)** | WSL2 Linux Subprocess | CLI subprocess (`wsl yara ...`) | Custom rule signature scanning for executables & scripts |

---

## 10. Known Gaps and Incomplete Items

A factual code audit revealed the following pending roadmap items and code-level gaps:

1. **Frontend Not Started:**
   * The `frontend/` directory in the repository root is present but completely empty.
2. **Tier 3 Multi-Modality ML Anomaly Models (Fixes 6 & 7):**
   * Training DICOM data (940 files across CT, MR, PT, US) has been downloaded to `backend/datasets/training/`, but per-modality Isolation Forest models (`models/if_<MODALITY>.pkl`) and dual compression-aware entropy baselines (`models/entropy_compressed.txt`) are not yet trained and integrated.
3. **Dependency List Gap in `requirements.txt`:**
   * `pyClamd` and `cryptography` are installed in the virtual environment and imported in code, but were missing from the static `requirements.txt` file.
4. **Auth Modernization (Tier 5 Fixes 11 & 12):**
   * [`backend/auth.py`](file:///d:/OrthoShield/backend/auth.py) currently relies on `python-jose` and `passlib`. Upgrading to `PyJWT` and direct `bcrypt` calls remains pending.
5. **Login Brute-Force Rate Limiting (Tier 5 Fix 14):**
   * Rate limiting (`slowapi`) and account lockout (`failed_attempts`, `locked_until`) are not yet implemented on `/login`.
6. **Token Blacklist Purge (Tier 5 Fix 15):**
   * `token_blacklist` currently stores revoked JTIs indefinitely without an automatic TTL-based cleanup task.
7. **Orthanc Forwarding Retry Worker:**
   * If Orthanc is offline during upload, the gateway logs `UPLOAD_CLEAN_FORWARD_FAILED` and retains the file in `uploads/`, but there is currently no background daemon to automatically retry forwarding queued files.

---

## 11. How to Run the Project Locally

Assuming a fresh clone on Windows with WSL2 and Docker Desktop installed:

### Step 1: Start External Daemons (WSL2 & Docker)
1. **Start ClamAV inside WSL2:**
   ```bash
   wsl sudo service clamav-daemon start
   # Verify port 3310 is listening:
   wsl ss -tulpn | grep 3310
   ```
2. **Start the Orthanc PACS Docker Container:**
   ```powershell
   docker run -d --name orthanc-server -p 127.0.0.1:9042:8042 -e ORTHANC_NAME="Orthanc inside Docker" jodogne/orthanc-plugins
   ```

### Step 2: Configure Environment
1. Copy template and configure `.env`:
   ```powershell
   cd backend
   Copy-Item .env.example .env
   ```
2. Update `CLAMAV_HOST` in `backend/.env` with your WSL IP address (`wsl hostname -I`).

### Step 3: Start the OrthoShield Backend Gateway
1. **Activate Python Virtual Environment & Install Dependencies:**
   ```powershell
   cd d:\OrthoShield
   .\venv\Scripts\Activate.ps1
   pip install -r backend/requirements.txt
   ```
2. **Start the FastAPI Application via Uvicorn:**
   ```powershell
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
3. **Access Interactive Swagger Docs:**
   * Navigate to `http://localhost:8000/docs` in your browser.

### Step 4: (Optional) Run the Surveillance Watcher
In a separate terminal:
```powershell
cd d:\OrthoShield\backend
python watcher.py
```
