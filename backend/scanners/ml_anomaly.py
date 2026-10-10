"""
Three-way distinction at load time:

  _missing_file = True   → FileNotFoundError: files simply not deployed yet.
                           check_ml_anomaly returns scanner_available=True, skipped=True.
                           Rationale: a missing .pkl is a deployment gap, not a security
                           signal.  The check is excluded from the denominator entirely —
                           it does not raise the score or trigger fail-closed quarantine.

  _corrupt_load = True   → Model files exist but failed to load (corrupt .pkl, joblib
                           version mismatch, truncated file, etc.).
                           check_ml_anomaly returns scanner_available=False, skipped=False.
                           Rationale: a file that exists but cannot be read could indicate
                           tampering.  Fail closed — same as ClamAV going offline.

  _model_loaded = True   → Happy path: model loaded, inference runs normally.

Runtime exceptions during scoring (numpy error, bad feature shape, etc.) also
return scanner_available=False because an unexpected crash in a functioning model
is a different risk class from "the file was never there."
"""
import os
import numpy as np
import joblib
from scipy.stats import entropy as scipy_entropy

BASE_DIR           = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH         = os.path.join(BASE_DIR, "isolation_forest_model.pkl")
THRESHOLD_PATH     = os.path.join(BASE_DIR, "anomaly_threshold.txt")
ENTROPY_STATS_PATH = os.path.join(BASE_DIR, "entropy_stats.txt")

_model_loaded = False
_missing_file = False
_corrupt_load = False
_load_error   = ""

try:
    # ── Stage 1: load model file ─────────────────────────────────────────────
    try:
        _model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        _missing_file = True
        _load_error   = f"Model file not found: {MODEL_PATH}"
        raise  # jump to outer except so we skip stages 2-3

    # ── Stage 2: load threshold ───────────────────────────────────────────────
    with open(THRESHOLD_PATH) as f:
        _threshold = float(f.read().strip())

    # ── Stage 3: load entropy statistics ─────────────────────────────────────
    with open(ENTROPY_STATS_PATH) as f:
        _entropy_mean, _entropy_std, _entropy_max = map(float, f.read().strip().split(","))

    _model_loaded = True

except FileNotFoundError:
    pass  # _missing_file already set above

except Exception as e:
    # Files exist but could not be loaded — treat as corruption / tamper risk
    _corrupt_load = True
    _load_error   = str(e)


def calculate_file_entropy(file_bytes: bytes) -> float:
    if len(file_bytes) == 0:
        return 0.0
    byte_counts   = np.bincount(np.frombuffer(file_bytes, dtype=np.uint8), minlength=256)
    probabilities = byte_counts / len(file_bytes)
    probabilities = probabilities[probabilities > 0]
    return float(scipy_entropy(probabilities, base=2))


def check_ml_anomaly(file_path: str, metadata: dict) -> dict:
    """
    Check 12: Isolation Forest + entropy Z-score anomaly detection.

    Return shape: {name, passed, scanner_available, skipped, detail}

    Cases
    ─────
    _missing_file   → skipped=True  (deployment gap, not a security signal)
    _corrupt_load   → scanner_available=False  (potential tampering, fail closed)
    invalid DICOM   → skipped=True  (features would be meaningless)
    inference error → scanner_available=False  (unexpected crash in live model)
    normal          → scored normally
    """

    # ── Model file absent: skip gracefully ───────────────────────────────────
    if _missing_file:
        return {
            "name":              "ml_anomaly_score",
            "passed":            True,
            "scanner_available": True,
            "skipped":           True,
            "detail":            f"ML model not deployed — check skipped ({_load_error})",
        }

    # ── Model file exists but corrupt: fail closed ───────────────────────────
    if _corrupt_load:
        return {
            "name":              "ml_anomaly_score",
            "passed":            True,
            "scanner_available": False,
            "skipped":           False,
            "detail":            f"ML model failed to load — possible corruption ({_load_error})",
        }

    # ── Structurally invalid DICOM: features meaningless ─────────────────────
    if not metadata.get("is_valid_dicom", False):
        return {
            "name":              "ml_anomaly_score",
            "passed":            True,
            "scanner_available": True,
            "skipped":           True,
            "detail":            "Skipped — file failed structural validation",
        }

    result = {
        "name":              "ml_anomaly_score",
        "passed":            True,
        "scanner_available": True,
        "skipped":           False,
        "detail":            "",
    }

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        file_entropy = calculate_file_entropy(file_bytes)

        pixel_data_len    = metadata.get("pixel_data_length", 0)
        header_len        = len(file_bytes) - pixel_data_len
        pixel_header_ratio = pixel_data_len / header_len if header_len > 0 else 0

        expected_tags = [
            "sop_instance_uid", "sop_class_uid", "modality", "rows", "columns",
            "bits_allocated", "pixel_data_present", "study_date",
            "manufacturer", "study_description",
        ]
        present_count = sum(
            1 for tag in expected_tags
            if metadata.get(tag) not in [None, "None", ""]
        )
        completeness_ratio = present_count / len(expected_tags)

        X = np.array([[
            len(file_bytes),
            file_entropy,
            metadata.get("total_tag_count", 0),
            completeness_ratio,
            pixel_header_ratio,
        ]])

        score     = _model.decision_function(X)[0]
        if_anomaly = score < _threshold

        z_score       = (file_entropy - _entropy_mean) / _entropy_std if _entropy_std > 0 else 0
        entropy_anomaly = (z_score > 3) or (file_entropy > _entropy_max)
        is_anomaly      = if_anomaly or entropy_anomaly

        if is_anomaly:
            reasons = []
            if if_anomaly:
                reasons.append(f"IF score {score:.4f} < threshold {_threshold:.4f}")
            if entropy_anomaly:
                reasons.append(
                    f"entropy {file_entropy:.3f} abnormal "
                    f"(z={z_score:.2f}, training max {_entropy_max:.3f})"
                )
            result["passed"] = False
            result["detail"] = f"Statistical anomaly: {'; '.join(reasons)}"
        else:
            result["detail"] = (
                f"Within normal range (IF score={score:.4f}, "
                f"entropy={file_entropy:.3f}, z={z_score:.2f})"
            )

    except Exception as e:
        # Unexpected crash in a model that loaded successfully — fail closed.
        # Different risk class from "the file was never there."
        result["scanner_available"] = False
        result["skipped"]           = False
        result["detail"]            = f"ML inference error — failing closed: {e}"

    return result