import os
import shutil
import numpy as np
import pydicom

SOURCE_FILE = "uploads/1-13.dcm"  # apni koi clean file ka naam yahan confirm kar lein
OUTPUT_DIR = "test_anomalies"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_corrupted_header():
    """Removes DICOM magic bytes — should fail magic_byte_structure"""
    with open(SOURCE_FILE, "rb") as f:
        data = f.read()
    output_path = os.path.join(OUTPUT_DIR, "anomaly_corrupted_header.dcm")
    with open(output_path, "wb") as f:
        f.write(data[200:])
    print(f"Created: {output_path}")


def generate_high_entropy_pixels():
    """Replaces pixel data with random noise — stays structurally valid, content anomalous"""
    ds = pydicom.dcmread(SOURCE_FILE)
    noise = np.random.randint(0, 256, size=len(ds.PixelData), dtype=np.uint8).tobytes()
    ds.PixelData = noise
    output_path = os.path.join(OUTPUT_DIR, "anomaly_high_entropy.dcm")
    ds.save_as(output_path)
    print(f"Created: {output_path}")


def generate_missing_tag():
    """Deletes Modality tag — should fail required_tags check"""
    ds = pydicom.dcmread(SOURCE_FILE)
    if "Modality" in ds:
        del ds.Modality
    output_path = os.path.join(OUTPUT_DIR, "anomaly_missing_tag.dcm")
    ds.save_as(output_path)
    print(f"Created: {output_path}")


def generate_future_date():
    """Sets StudyDate to year 2099 — should fail timestamp_validity check"""
    ds = pydicom.dcmread(SOURCE_FILE)
    ds.StudyDate = "20991231"
    output_path = os.path.join(OUTPUT_DIR, "anomaly_future_date.dcm")
    ds.save_as(output_path)
    print(f"Created: {output_path}")


def generate_injection_metadata():
    """Injects SQLi-style text into StudyDescription — should fail injection_patterns check"""
    ds = pydicom.dcmread(SOURCE_FILE)
    ds.StudyDescription = "test' OR 1=1--"
    output_path = os.path.join(OUTPUT_DIR, "anomaly_injection.dcm")
    ds.save_as(output_path)
    print(f"Created: {output_path}")


def generate_duplicate_copy():
    """Exact valid copy — should trigger duplicate_detection on second upload"""
    output_path = os.path.join(OUTPUT_DIR, "anomaly_duplicate_copy.dcm")
    shutil.copy(SOURCE_FILE, output_path)
    print(f"Created: {output_path}")


def generate_suspicious_filename():
    """Copies clean file but with a path-traversal-style filename"""
    output_path = os.path.join(OUTPUT_DIR, "..evil_traversal_test.dcm")
    shutil.copy(SOURCE_FILE, output_path)
    print(f"Created (upload this filename manually to test path traversal): {output_path}")


if __name__ == "__main__":
    print(f"Generating synthetic anomalies from: {SOURCE_FILE}\n")
    generate_corrupted_header()
    generate_high_entropy_pixels()
    generate_missing_tag()
    generate_future_date()
    generate_injection_metadata()
    generate_duplicate_copy()
    generate_suspicious_filename()
    print(f"\nDone. Check the '{OUTPUT_DIR}' folder.")