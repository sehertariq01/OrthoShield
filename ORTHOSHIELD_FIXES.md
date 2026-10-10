# OrthoShield — Fix Guide

Ordered by what breaks the project if left alone. Fix 1–3 before anyone else sees this run.

---

# TIER 1 — Fix today

## Fix 1. Stop uploading patient files to VirusTotal

**File:** `scanners/virustotal_scan.py`

**Problem:** you fall back to uploading the actual DICOM file when the hash is unknown. That file contains PatientName, PatientID, birth date, institution, and the image. Public VT shares submissions with researchers and paying customers.

**Rule:** hash lookup only. Never `POST /files`.

```python
import requests
from config import VT_API_KEY

VT_URL = "https://www.virustotal.com/api/v3/files/{}"


def check_virustotal(file_hash: str) -> dict:
    """
    Hash-only VirusTotal lookup. The file body is NEVER transmitted —
    DICOM files contain PHI and uploading them is a disclosure event.
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
        # Hash unknown to VT. This is the NORMAL case for a private
        # hospital study and is NOT a finding. Do not upload.
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
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    total = sum(stats.values())

    if malicious > 0 or suspicious > 2:
        result["passed"] = False
        result["detail"] = f"{malicious} malicious / {suspicious} suspicious of {total} engines"
    else:
        result["detail"] = f"0/{total} engines flagged"

    return result
```

**Also update your documentation.** Section 15 claims "file actually run in VT sandbox." Once this fix lands that is no longer true, and it was the only genuinely dynamic step in the pipeline. See Fix 8.

---

## Fix 2. Fail closed when a scanner is unavailable

**Problem:** your own test log shows `ClamAV unreachable (WSL off)` and the file was released as CLEAN. Right now every scanner returns a two-state `passed: True/False`, so "didn't run" is indistinguishable from "ran and found nothing."

### Step A — three states, not two

Every scanner returns `scanner_available`. Update `malware_scan.py`, `yara_scan.py`, `virustotal_scan.py`:

```python
# scanners/malware_scan.py
def scan_file_for_malware(file_path: str) -> dict:
    result = {"name": "malware_scan", "passed": True, "scanner_available": True, "detail": ""}
    try:
        cd = pyclamd.ClamdNetworkSocket(host=CLAMAV_HOST, port=3310)
        if not cd.ping():
            raise ConnectionError("ClamAV daemon did not respond to ping")
    except Exception as e:
        result["scanner_available"] = False
        result["detail"] = f"ClamAV unavailable: {e}"
        return result

    wsl_path = to_wsl_path(file_path)
    scan = cd.scan_file(wsl_path)
    if scan:
        result["passed"] = False
        result["detail"] = f"ClamAV signature match: {list(scan.values())[0]}"
    else:
        result["detail"] = "No signature match"
    return result
```

### Step B — the scoring engine acts on it

**File:** `scanners/scoring_engine.py`

```python
DEGRADED_MODE = "quarantine"   # "quarantine" = fail closed | "flag" = allow but mark

def evaluate(check_results: list[dict]) -> dict:
    unavailable = [c["name"] for c in check_results if not c.get("scanner_available", True)]

    if unavailable and DEGRADED_MODE == "quarantine":
        return {
            "risk_score": None,
            "decision": "BLOCKED",
            "reason": f"Scan incomplete — engines offline: {', '.join(unavailable)}",
            "incomplete_scan": True,
            "unavailable_engines": unavailable,
        }
    ...
```

A study held because ClamAV was down is *pending*, not *malicious* — it should be re-scannable once the engine is back (see Fix 10, `POST /scans/{id}/rescan`).

---

## Fix 3. Quarantine blocked files, don't delete them

**File:** `main.py`

**Problem:** `os.remove(file_path)` destroys the evidence you need for an incident report.

```python
import os, shutil, stat
from pathlib import Path

QUARANTINE_DIR = Path(__file__).parent / "quarantine"
QUARANTINE_DIR.mkdir(exist_ok=True)


def quarantine_file(file_path: str, file_hash: str) -> str:
    """
    Move a blocked file to isolated storage, read-only, named by hash so
    it cannot collide or be re-executed by extension.
    """
    dest = QUARANTINE_DIR / f"{file_hash}.quarantine"
    shutil.move(file_path, dest)
    os.chmod(dest, stat.S_IRUSR)   # owner read-only, no execute bit
    return str(dest)
```

In the upload route, replace the delete:

```python
if decision == "BLOCKED":
    quarantine_path = quarantine_file(file_path, file_hash)
    scan_log.quarantine_path = quarantine_path      # new column, see below
    db.commit()
```

**Migration** — add to `models.py` `ScanLog`:

```python
quarantine_path = Column(String(500), nullable=True)
incomplete_scan = Column(Boolean, default=False)
```

```sql
ALTER TABLE scan_logs ADD COLUMN quarantine_path VARCHAR(500);
ALTER TABLE scan_logs ADD COLUMN incomplete_scan BOOLEAN DEFAULT 0;
```

Add `quarantine/` to `.gitignore`, and exclude it from any antivirus auto-clean so ClamAV doesn't delete your evidence.

---

# TIER 2 — Scoring logic

## Fix 4. Make the risk score actually reachable

**File:** `scanners/scoring_engine.py`

**Problem:** dividing by 178 (the sum of every weight) means one failed non-hard-block check tops out at ~17% and most land at 3–6%. Threshold is 25. So only hard blocks block. Your own test proves it: missing required tag **plus** a duplicate hit scored 8.43 → CLEAN.

**Fix:** divide by the weights of the checks that actually *ran*, and lower the threshold.

```python
WEIGHTS = {
    "malware_scan": 30, "virustotal": 25, "yara_scan": 20,
    "embedded_objects": 20, "ml_anomaly_score": 15, "magic_byte_structure": 15,
    "replay_detection": 15, "path_traversal": 10, "injection_patterns": 8,
    "required_tags": 5, "uid_format": 5, "timestamp_validity": 5,
    "pixel_data_consistency": 5, "file_size_limit": 5,
}

HARD_BLOCK = {"magic_byte_structure", "malware_scan", "yara_scan", "virustotal", "path_traversal"}
BLOCK_THRESHOLD = 20


def evaluate(check_results: list[dict]) -> dict:
    ran = [c for c in check_results
           if c.get("scanner_available", True) and not c.get("skipped", False)]

    denominator = sum(WEIGHTS[c["name"]] for c in ran) or 1
    failed_weight = sum(WEIGHTS[c["name"]] for c in ran if not c["passed"])
    risk_score = round((failed_weight / denominator) * 100, 2)

    hard = [c["name"] for c in ran if not c["passed"] and c["name"] in HARD_BLOCK]

    if hard:
        decision, reason = "BLOCKED", f"Hard-block check failed: {', '.join(hard)}"
    elif risk_score >= BLOCK_THRESHOLD:
        decision, reason = "BLOCKED", f"Risk score {risk_score} >= {BLOCK_THRESHOLD}"
    else:
        decision, reason = "CLEAN", "Passed all applicable checks"

    return {"risk_score": risk_score, "decision": decision, "reason": reason,
            "checks_run": len(ran), "checks_failed": len([c for c in ran if not c['passed']])}
```

Now that same test file scores `5 / 158 × 100 = 3.16` for the missing tag alone, and a real injection + anomaly + embedded-object combination (43/158 = 27%) blocks as it should. `path_traversal` is promoted to hard-block — there is no benign reason for `../` in a filename.

**Re-run your test corpus after this change.** The threshold wants tuning against real files, not guessed.

---

## Fix 5. Split duplicate from replay

**File:** `main.py` → `check_duplicate()`

**Problem:** hospitals re-send identical studies constantly — retries, network drops, PACS routing loops. Identical hash is a *dedupe*, not an attack. Same SOPInstanceUID with *different* bytes is the actual tamper signal.

```python
def check_replay(db, file_hash: str, sop_instance_uid: str) -> dict:
    result = {"name": "replay_detection", "passed": True, "detail": "", "is_duplicate": False}

    exact = db.query(ScanLog).filter(ScanLog.file_hash == file_hash).first()
    if exact:
        # Benign: same study sent twice. Note it, don't penalise it.
        result["is_duplicate"] = True
        result["detail"] = f"Identical file previously scanned (scan_log id={exact.id}) — benign resend"
        return result

    if sop_instance_uid:
        conflict = (db.query(SHA256Store)
                      .filter(SHA256Store.sop_instance_uid == sop_instance_uid,
                              SHA256Store.file_hash != file_hash)
                      .first())
        if conflict:
            # Same scan identity, different bytes. Tamper or replay.
            result["passed"] = False
            result["detail"] = (f"SOPInstanceUID {sop_instance_uid} already recorded under a "
                                f"different hash — content differs from the original study")
    return result
```

Rename the check `duplicate_detection` → `replay_detection` everywhere and give it weight 15, since it now only fires on a genuine tamper signal.

---

# TIER 3 — ML model

## Fix 6. Train across modalities

**Problem:** MRA head/neck + prostate are both MR. An Isolation Forest that has only ever seen MR will flag every CT, US, CR, and DX study as anomalous on file size, tag count, and pixel/header ratio alone.

Two options — pick one:

**Option A (better, more work): per-modality models.** Modality is a strong natural partition; file size and tag counts differ by an order of magnitude between US and CT.

```python
# train_isolation_forest.py
for modality, group in df.groupby("modality"):
    if len(group) < 50:
        print(f"Skipping {modality}: only {len(group)} samples, need >= 50")
        continue
    model = IsolationForest(n_estimators=200, max_samples=64,
                            contamination=0.05, random_state=42)
    X = group[FEATURES]
    model.fit(X)
    joblib.dump(model, f"models/if_{modality}.pkl")
    scores = model.decision_function(X)
    Path(f"models/threshold_{modality}.txt").write_text(str(np.percentile(scores, 5)))
```

```python
# ml_anomaly.py
def check_ml_anomaly(file_path, metadata):
    modality = metadata.get("modality")
    model_path = f"models/if_{modality}.pkl"
    if not os.path.exists(model_path):
        return {"name": "ml_anomaly_score", "passed": True, "skipped": True,
                "detail": f"No trained model for modality {modality}"}
    ...
```

Note the `skipped: True` — Fix 4's scoring engine drops skipped checks from the denominator rather than silently passing them.

**Option B (quick): add modality as a feature** and gather a mixed corpus. Weaker, because Isolation Forest treats the one-hot modality columns as just more numeric dimensions, but it beats a single-modality model.

Either way you need non-MR training data. The TCIA public archives have free CT, CR, and US collections.

---

## Fix 7. Make entropy compression-aware

**File:** `scanners/ml_anomaly.py`

**Problem:** compressed pixel data (JPEG2000, RLE) pushes Shannon entropy to ~8.0. If your training corpus was uncompressed, every compressed study trips `Z > 3`. You already compute `is_compressed` in the parser — carry it through.

Train two sets of stats:

```python
# train_isolation_forest.py
for label, group in [("uncompressed", df[~df.is_compressed]),
                     ("compressed",   df[df.is_compressed])]:
    if len(group) < 30:
        continue
    Path(f"models/entropy_{label}.txt").write_text(
        f"{group.entropy.mean()}\n{group.entropy.std()}\n{group.entropy.max()}"
    )
```

Use the matching set at inference:

```python
label = "compressed" if metadata.get("is_compressed") else "uncompressed"
stats_file = f"models/entropy_{label}.txt"
if not os.path.exists(stats_file):
    entropy_anomaly = False          # no baseline -> no claim
else:
    mean, std, emax = (float(x) for x in Path(stats_file).read_text().split())
    z = (entropy - mean) / std if std > 0 else 0
    entropy_anomaly = z > 3 or entropy > emax
```

If you have no compressed files in training at all, skip the entropy check for compressed uploads rather than guessing — same `skipped: True` pattern.

---

# TIER 4 — Accuracy of the write-up

## Fix 8. Correct the static/dynamic classification

This is the one an examiner will catch. Byte-signature and regex matching over a file is **static analysis** — nothing executes. After Fix 1, nothing in your pipeline is dynamic at all.

Rewrite Section 15 as:

> **All 14 checks are static analysis.** OrthoShield examines file structure, metadata, and raw bytes without executing the file. This is a deliberate constraint: DICOM files contain PHI, so submitting them to a live sandbox would constitute a disclosure. Check 13 queries VirusTotal's *existing* verdict for a file hash — a reputation lookup over prior analysis, not a fresh execution.
>
> **Dynamic analysis is documented as future work** and would require either an on-premise detonation environment or full de-identification before submission.

Rename check 14 from "Embedded Object Extraction (DYNAMIC)" to "Embedded Content Extraction (Static)."

Framing this as a *constraint you reasoned about* is stronger than claiming a capability you don't have.

## Fix 9. One canonical check order

You currently have three conflicting numbering schemes — Section 7, Section 14's test log, and Section 15's method table all disagree. Define the order once, in code, and generate the docs from it:

```python
# scanners/__init__.py
CHECK_ORDER = [
    "magic_byte_structure",     # 1
    "path_traversal",           # 2
    "file_size_limit",          # 3
    "required_tags",            # 4
    "uid_format",               # 5
    "timestamp_validity",       # 6
    "pixel_data_consistency",   # 7
    "injection_patterns",       # 8
    "replay_detection",         # 9
    "malware_scan",             # 10
    "yara_scan",                # 11
    "ml_anomaly_score",         # 12
    "virustotal",               # 13
    "embedded_objects",         # 14
]
```

Sort every result list by this before storing or displaying. Then fix Sections 7, 14, and 15 to match.

## Fix 10. Encapsulated PDF is legitimate DICOM

**File:** `scanners/embedded_extractor.py`

Structured reports and referral letters use Encapsulated PDF Storage daily. Flagging `%PDF` and tags `(0042,0011)`/`(0042,0012)` unconditionally false-positives on real clinical data.

```python
ENCAPSULATED_PDF_SOP = "1.2.840.10008.5.1.4.1.1.104.1"
ENCAPSULATED_CDA_SOP = "1.2.840.10008.5.1.4.1.1.104.2"
ENCAPSULATED_SOPS = {ENCAPSULATED_PDF_SOP, ENCAPSULATED_CDA_SOP}

def check_embedded_objects(file_path, metadata):
    sop_class = metadata.get("sop_class_uid", "")
    expects_encapsulated = sop_class in ENCAPSULATED_SOPS

    signatures = dict(DANGEROUS_SIGNATURES)
    if expects_encapsulated:
        signatures.pop(b"%PDF", None)   # declared and expected for this SOP class
    ...
```

Keep `MZ`, `ELF`, and the archive signatures flagged regardless — no SOP class legitimately encapsulates an executable.

---

# TIER 5 — Hardening

## Fix 11. passlib + bcrypt version break

passlib 1.7.4 reads `bcrypt.__about__`, removed in bcrypt 4.1+. With bcrypt 5.0 this raises on first hash. Drop passlib:

```python
# auth.py
import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
```

bcrypt truncates at 72 bytes — reject longer passwords at the schema layer rather than silently truncating:

```python
# schemas.py
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=12, max_length=72)
    role: Literal["admin", "analyst", "viewer"]
```

Existing hashes stay valid — both libraries produce standard `$2b$` output.

## Fix 12. Replace python-jose with PyJWT

python-jose is effectively unmaintained and has had CVEs (including algorithm-confusion issues). PyJWT is what FastAPI's own docs use now.

```python
# auth.py
import jwt, uuid
from datetime import datetime, timezone, timedelta
from jwt.exceptions import InvalidTokenError

ROLE_TTL = {"admin": 8, "analyst": 4, "viewer": 1}

def create_access_token(username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(hours=ROLE_TTL.get(role, 1)),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def decode_token(token: str) -> dict:
    # algorithms is a whitelist — never read the alg from the token header
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

`pip uninstall python-jose && pip install PyJWT`, update `requirements.txt`.

## Fix 13. Enforce the size limit while streaming

Checking size after the file is on disk means the DoS already landed.

```python
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
CHUNK = 1024 * 1024

async def save_upload_streaming(upload_file, dest_path: str) -> tuple[int, str]:
    hasher = hashlib.sha256()
    total = 0
    with open(dest_path, "wb") as out:
        while chunk := await upload_file.read(CHUNK):
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                out.close()
                os.remove(dest_path)
                raise HTTPException(413, "File exceeds 100 MB limit")
            hasher.update(chunk)
            out.write(chunk)
    return total, hasher.hexdigest()
```

Also cap it at the reverse proxy — nginx `client_max_body_size 100m;` — so oversized bodies never reach Python.

## Fix 14. Lock down `/login`

No rate limit and no lockout means brute-force is wide open. Also confirm `is_active` is actually checked — the docs never say it is.

```python
# pip install slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/login")
@limiter.limit("5/minute")
def login(request: Request, creds: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == creds.username).first()

    # Same error and same timing for "no such user" and "wrong password" —
    # otherwise the response tells an attacker which usernames exist.
    if not user or not verify_password(creds.password, user.password_hash):
        write_audit(db, "LOGIN_FAILED", creds.username, f"from {request.client.host}")
        raise HTTPException(401, "Invalid credentials")

    if not user.is_active:
        write_audit(db, "LOGIN_DENIED", user.username, "account disabled")
        raise HTTPException(403, "Account disabled")

    user.ip_address = request.client.host
    db.commit()
    write_audit(db, "LOGIN", user.username, f"from {request.client.host}")
    return {"access_token": create_access_token(user.username, user.role), "token_type": "bearer"}
```

Add lockout after repeated failures — a `failed_attempts` counter and `locked_until` timestamp on `users`, reset on success.

## Fix 15. Purge expired blacklist entries

`token_blacklist` grows forever and every request scans it. Once a token's own `exp` has passed the JWT is rejected anyway, so the row is dead weight.

```python
def purge_expired_blacklist(db):
    """Max token lifetime is 8h (admin), so anything older cannot still be valid."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=9)
    deleted = db.query(TokenBlacklist).filter(TokenBlacklist.revoked_at < cutoff).delete()
    db.commit()
    return deleted
```

Call it on startup and hourly. Add an index: `CREATE INDEX idx_blacklist_jti ON token_blacklist(token_jti);`

## Fix 16. Add the missing read endpoints

You built `alerts`, `audit_logs`, and `scan_logs` and gave the API no way to read any of them. An analyst literally cannot see the alerts the system raises. This is the biggest *functional* gap.

```python
@app.get("/scans")
def list_scans(skip: int = 0, limit: int = Query(50, le=200),
               decision: str | None = None,
               user = Depends(require_role(["admin", "analyst", "viewer"])),
               db: Session = Depends(get_db)):
    q = db.query(ScanLog)
    if decision:
        q = q.filter(ScanLog.decision == decision.upper())
    return q.order_by(ScanLog.created_at.desc()).offset(skip).limit(limit).all()


@app.get("/alerts")
def list_alerts(status: str = "OPEN", severity: str | None = None,
                user = Depends(require_role(["admin", "analyst"])),
                db: Session = Depends(get_db)):
    q = db.query(Alert).filter(Alert.status == status.upper())
    if severity:
        q = q.filter(Alert.severity == severity.upper())
    return q.order_by(Alert.created_at.desc()).limit(200).all()


@app.patch("/alerts/{alert_id}")
def resolve_alert(alert_id: int, new_status: Literal["RESOLVED", "IGNORED"],
                  user = Depends(require_role(["admin", "analyst"])),
                  db: Session = Depends(get_db)):
    alert = db.query(Alert).get(alert_id)
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.status = new_status
    alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    write_audit(db, "ALERT_UPDATED", user["username"], f"alert {alert_id} -> {new_status}")
    return alert


@app.post("/scans/{scan_id}/rescan")
def rescan(scan_id: int, user = Depends(require_role(["admin", "analyst"])),
           db: Session = Depends(get_db)):
    """Re-run a study that was held because an engine was offline (Fix 2)."""
    ...
```

## Fix 17. Prove the audit chain is intact

A hash chain nobody verifies is just a column. Add the verifier:

```python
@app.get("/audit/verify")
def verify_audit_chain(user = Depends(require_role(["admin"])),
                       db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.id).all()
    previous = "0" * 64
    for log in logs:
        expected = hashlib.sha256(
            f"{log.event}{log.username}{log.details}{previous}".encode()
        ).hexdigest()
        if log.previous_hash != previous or log.current_hash != expected:
            return {"valid": False, "broken_at_id": log.id,
                    "detail": "Chain integrity failure — entry altered or removed"}
        previous = log.current_hash
    return {"valid": True, "entries_verified": len(logs)}
```

Note the honest limit: whoever can write to `orthoshield.db` can recompute the whole chain. This detects *tampering by someone without app-level access*, not by a DB admin. Real tamper-evidence needs the chain head published somewhere append-only — write it to a WORM log or a separate host hourly. Say this in the docs rather than overclaiming.

## Fix 18. Clean up `uploads/` and finish or drop Orthanc

CLEAN files are never removed, so the directory fills indefinitely:

```python
if decision == "CLEAN":
    forwarded = forward_to_orthanc(file_path)
    if forwarded:
        os.remove(file_path)     # PACS has it now
    else:
        logger.error("Orthanc forward failed, retaining %s for retry", file_path)
```

And Orthanc forwarding is in your architecture diagram with no client module in the folder structure. Either write it:

```python
# scanners/orthanc_client.py
def forward_to_orthanc(file_path: str) -> bool:
    with open(file_path, "rb") as f:
        r = requests.post(f"{ORTHANC_URL}/instances", data=f,
                          auth=(ORTHANC_USER, ORTHANC_PASS), timeout=30)
    return r.status_code in (200, 201)
```

…or remove it from the diagram and label it future work. A diagram that shows something the code doesn't do is the kind of thing that unravels a viva.

---

# Suggested order

| Session | Do |
|---|---|
| 1 | Fixes 1, 2, 3 — PHI leak, fail-closed, quarantine |
| 2 | Fixes 4, 5 — scoring maths, replay vs duplicate. **Re-run your test corpus and retune the threshold.** |
| 3 | Fixes 11, 12, 13, 14, 15 — dependency and auth hardening (mostly mechanical) |
| 4 | Fixes 16, 17, 18 — the missing read API, chain verifier, Orthanc |
| 5 | Fixes 6, 7 — retrain with mixed-modality data |
| 6 | Fixes 8, 9, 10 — documentation accuracy pass |

Tier 1 and 2 change behaviour, so re-run your full test corpus after each and record the before/after scores. That comparison table is worth having in the report on its own — it shows the tuning was evidence-driven rather than guessed.
