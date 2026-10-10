import numpy as np
import pandas as pd
import joblib
import pydicom
from scipy.stats import entropy as scipy_entropy

TARGET_FILE = "test_anomalies/anomaly_high_entropy.dcm"
FEATURES_CSV = "ml_features.csv"
MODEL_PATH = "isolation_forest_model.pkl"
FEATURE_COLUMNS = ["file_size", "entropy", "total_tags", "completeness_ratio", "pixel_header_ratio"]


def calculate_file_entropy(file_bytes: bytes) -> float:
    byte_counts = np.bincount(np.frombuffer(file_bytes, dtype=np.uint8), minlength=256)
    probabilities = byte_counts / len(file_bytes)
    probabilities = probabilities[probabilities > 0]
    return float(scipy_entropy(probabilities, base=2))


# Load target file
with open(TARGET_FILE, "rb") as f:
    file_bytes = f.read()

ds = pydicom.dcmread(TARGET_FILE)
file_entropy = calculate_file_entropy(file_bytes)
total_tags = len(ds)

expected_tags = [
    "SOPInstanceUID", "SOPClassUID", "Modality", "Rows", "Columns",
    "BitsAllocated", "PixelData", "StudyDate", "Manufacturer", "StudyDescription"
]
present_count = sum(1 for tag in expected_tags if hasattr(ds, tag))
completeness_ratio = present_count / len(expected_tags)

pixel_data_len = len(ds.PixelData) if hasattr(ds, "PixelData") else 0
header_len = len(file_bytes) - pixel_data_len
pixel_header_ratio = pixel_data_len / header_len if header_len > 0 else 0

print("=== anomaly_high_entropy.dcm feature values ===")
print(f"file_size:           {len(file_bytes)}")
print(f"entropy:              {file_entropy:.4f}")
print(f"total_tags:           {total_tags}")
print(f"completeness_ratio:   {completeness_ratio:.4f}")
print(f"pixel_header_ratio:   {pixel_header_ratio:.4f}")

print("\n=== Training data entropy distribution ===")
df = pd.read_csv(FEATURES_CSV)
print(df["entropy"].describe())

print("\n=== Percentile rank of this file's entropy within training data ===")
percentile = (df["entropy"] < file_entropy).mean() * 100
print(f"This file's entropy is higher than {percentile:.1f}% of training samples")

# Check decision function contribution
model = joblib.load(MODEL_PATH)
X = np.array([[len(file_bytes), file_entropy, total_tags, completeness_ratio, pixel_header_ratio]])
score = model.decision_function(X)[0]
print(f"\nFinal Isolation Forest score: {score:.4f}")