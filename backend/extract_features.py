import os
import glob
import numpy as np
import pandas as pd
import pydicom
from scipy.stats import entropy as scipy_entropy

# ============================================================
# CONFIGURATION - confirmed dataset paths
# ============================================================
DATASET_DIRS = [
    r"D:\OrthoShield\datasets\MRA-Head_and_Neck",
    r"D:\OrthoShield\datasets\prostate",
    r"D:\OrthoShield\datasets\archive",
]

OUTPUT_CSV = "ml_features.csv"


def calculate_file_entropy(file_bytes: bytes) -> float:
    """
    Shannon entropy of the raw file bytes.
    Normal medical images typically fall in a predictable range (~6.0-7.5).
    Encrypted/packed/random content pushes this close to 8.0 (max).
    """
    if len(file_bytes) == 0:
        return 0.0

    byte_counts = np.bincount(np.frombuffer(file_bytes, dtype=np.uint8), minlength=256)
    probabilities = byte_counts / len(file_bytes)
    probabilities = probabilities[probabilities > 0]
    return float(scipy_entropy(probabilities, base=2))


def extract_features_from_file(file_path: str) -> dict:
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        ds = pydicom.dcmread(file_path, force=False)

        # Skip compressed-transfer-syntax files for training:
        # compressed pixel data has inherently high entropy that is not
        # comparable to raw/uncompressed scan data, and would distort
        # the entropy feature's ability to flag genuine anomalies.
        if hasattr(ds, "file_meta") and hasattr(ds.file_meta, "TransferSyntaxUID"):
            try:
                if ds.file_meta.TransferSyntaxUID.is_compressed:
                    return None
            except Exception:
                pass

    except Exception:
        return None

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
        "filename": os.path.basename(file_path),
        "file_size": file_size,
        "entropy": file_entropy,
        "total_tags": total_tags,
        "completeness_ratio": completeness_ratio,
        "pixel_header_ratio": pixel_header_ratio,
    }


def main():
    all_features = []
    skipped = 0

    for dataset_dir in DATASET_DIRS:
        if not os.path.isdir(dataset_dir):
            print(f"WARNING: directory not found, skipping: {dataset_dir}")
            continue

        for root, _, files in os.walk(dataset_dir):
            for fname in files:
                file_path = os.path.join(root, fname)
                features = extract_features_from_file(file_path)

                if features is None:
                    skipped += 1
                    continue

                all_features.append(features)

    if not all_features:
        print("ERROR: No valid DICOM files found. Check DATASET_DIRS path.")
        return

    df = pd.DataFrame(all_features)
    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\nExtracted features from {len(all_features)} files.")
    print(f"Skipped (unreadable/non-DICOM): {skipped} files.")
    print(f"Saved to: {OUTPUT_CSV}\n")
    print("Feature summary:")
    print(df.describe())


if __name__ == "__main__":
    main()