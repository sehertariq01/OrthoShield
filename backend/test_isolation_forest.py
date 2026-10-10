import os
import numpy as np
import joblib
import pydicom
from scipy.stats import entropy as scipy_entropy

MODEL_PATH = "isolation_forest_model.pkl"
SCALER_PATH = "feature_scaler.pkl"
ANOMALY_DIR = "test_anomalies"
FEATURE_COLUMNS = ["file_size", "entropy", "total_tags", "completeness_ratio", "pixel_header_ratio"]


def calculate_file_entropy(file_bytes: bytes) -> float:
    if len(file_bytes) == 0:
        return 0.0
    byte_counts = np.bincount(np.frombuffer(file_bytes, dtype=np.uint8), minlength=256)
    probabilities = byte_counts / len(file_bytes)
    probabilities = probabilities[probabilities > 0]
    return float(scipy_entropy(probabilities, base=2))


def extract_features_from_file(file_path: str):
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        ds = pydicom.dcmread(file_path, force=False)
    except Exception as e:
        return None, str(e)

    file_size = len(file_bytes)
    file_entropy = calculate_file_entropy(file_bytes)
    total_tags = len(ds)

    expected_tags = [
        "SOPInstanceUID", "SOPClassUID", "Modality", "Rows", "Columns",
        "BitsAllocated", "PixelData", "StudyDate", "Manufacturer", "StudyDescription"
    ]
    present_count = sum(1 for tag in expected_tags if hasattr(ds, tag))
    completeness_ratio = present_count / len(expected_tags)

    pixel_data_len = len(ds.PixelData) if hasattr(ds, "PixelData") else 0
    header_len = file_size - pixel_data_len
    pixel_header_ratio = pixel_data_len / header_len if header_len > 0 else 0

    return {
        "file_size": file_size,
        "entropy": file_entropy,
        "total_tags": total_tags,
        "completeness_ratio": completeness_ratio,
        "pixel_header_ratio": pixel_header_ratio,
    }, None
def main():
    model = joblib.load(MODEL_PATH)
    with open("anomaly_threshold.txt") as f:
        threshold = float(f.read().strip())
    with open("entropy_stats.txt") as f:
        entropy_mean, entropy_std, entropy_max = map(float, f.read().strip().split(","))

    print(f"{'File':<40} {'IF Score':>10}  {'Entropy':>8}  {'Verdict':<10}")
    print("-" * 80)

    for fname in sorted(os.listdir(ANOMALY_DIR)):
        file_path = os.path.join(ANOMALY_DIR, fname)
        features, error = extract_features_from_file(file_path)

        if features is None:
            print(f"{fname:<40} {'N/A':>10}  {'N/A':>8}  SKIPPED (not valid DICOM)")
            continue

        X = np.array([[features[col] for col in FEATURE_COLUMNS]])
        score = model.decision_function(X)[0]

        # Isolation Forest verdict (multivariate)
        if_anomaly = score < threshold

        # Univariate safety-net: entropy Z-score check
        entropy_val = features["entropy"]
        z_score = (entropy_val - entropy_mean) / entropy_std if entropy_std > 0 else 0
        entropy_anomaly = (z_score > 3) or (entropy_val > entropy_max)

        is_anomaly = if_anomaly or entropy_anomaly
        verdict = "ANOMALY" if is_anomaly else "normal"

        print(f"{fname:<40} {score:>10.4f}  {entropy_val:>8.3f}  {verdict:<10}")


if __name__ == "__main__":
    main()

