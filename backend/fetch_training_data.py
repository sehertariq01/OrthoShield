"""
fetch_training_data.py — pull mixed-modality DICOM from TCIA for OrthoShield.

Your Isolation Forest was trained on MR only (MRA head/neck + prostate), so it
flags every CT, CR, and US study as anomalous on file size and tag count alone.
This script grabs a balanced sample across modalities to retrain against.

No account needed — these are public collections. No GUI, no NBIA Data
Retriever; it talks to the public REST API directly.

Usage:
    pip install requests
    python fetch_training_data.py                    # ~4 series per modality
    python fetch_training_data.py --per-modality 8   # more data, slower
    python fetch_training_data.py --modalities CT US

Output:
    datasets/training/<MODALITY>/<SeriesInstanceUID>/*.dcm
    datasets/training/manifest.csv
"""

import argparse
import csv
import io
import sys
import time
import zipfile
from pathlib import Path

import requests

API = "https://services.cancerimagingarchive.net/nbia-api/services/v1"
OUT_DIR = Path(__file__).resolve().parent / "datasets" / "training"

# Public collections chosen for modality spread. CPTAC collections are small
# per-series, which keeps the download manageable.
COLLECTIONS = {
    "CT": ["CPTAC-LSCC", "CPTAC-PDA", "TCGA-LUAD"],
    "CR": ["CPTAC-LSCC", "TCGA-LUAD"],          # computed radiography / plain film
    "DX": ["CPTAC-LUAD", "CPTAC-LSCC"],          # digital radiography
    "US": ["CPTAC-PDA", "CPTAC-UCEC"],           # ultrasound
    "PT": ["CPTAC-LSCC", "TCGA-LUAD"],           # PET
    "MR": ["CPTAC-UCEC"],                        # a little more MR for balance
}

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "OrthoShield-training-fetch/1.0"})


def get_series(collection: str, modality: str) -> list[dict]:
    """List available series for a collection + modality."""
    try:
        r = SESSION.get(
            f"{API}/getSeries",
            params={"Collection": collection, "Modality": modality},
            timeout=60,
        )
        r.raise_for_status()
        return r.json() if r.text.strip() else []
    except requests.RequestException as e:
        print(f"    [warn] {collection}/{modality}: {e}")
        return []


def download_series(series_uid: str, dest: Path) -> int:
    """Download one series as a zip and extract the .dcm files. Returns file count."""
    dest.mkdir(parents=True, exist_ok=True)
    try:
        r = SESSION.get(
            f"{API}/getImage",
            params={"SeriesInstanceUID": series_uid},
            timeout=600,
            stream=True,
        )
        r.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            members = [m for m in z.namelist() if m.lower().endswith(".dcm")]
            for m in members:
                z.extract(m, dest)
        return len(members)
    except (requests.RequestException, zipfile.BadZipFile) as e:
        print(f"    [warn] series {series_uid[:24]}...: {e}")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-modality", type=int, default=4,
                    help="series to fetch per modality (default 4)")
    ap.add_argument("--modalities", nargs="+", default=list(COLLECTIONS),
                    help="subset of modalities to fetch")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    total_files = 0

    for modality in args.modalities:
        if modality not in COLLECTIONS:
            print(f"[skip] unknown modality {modality}")
            continue

        print(f"\n=== {modality} ===")
        collected = 0

        for collection in COLLECTIONS[modality]:
            if collected >= args.per_modality:
                break

            print(f"  querying {collection}...")
            series_list = get_series(collection, modality)
            if not series_list:
                continue

            # Prefer small series so the download stays reasonable
            series_list.sort(key=lambda s: int(s.get("ImageCount", 9999) or 9999))

            for series in series_list:
                if collected >= args.per_modality:
                    break

                uid = series.get("SeriesInstanceUID")
                count = series.get("ImageCount", "?")
                if not uid:
                    continue

                dest = OUT_DIR / modality / uid[-16:]
                if dest.exists() and any(dest.rglob("*.dcm")):
                    print(f"    [have] {uid[-16:]}")
                    collected += 1
                    continue

                print(f"    downloading {uid[-16:]} ({count} images)...", end=" ", flush=True)
                n = download_series(uid, dest)
                print(f"{n} files")

                if n:
                    collected += 1
                    total_files += n
                    manifest_rows.append({
                        "modality": modality,
                        "collection": collection,
                        "series_uid": uid,
                        "image_count": n,
                        "path": str(dest.relative_to(OUT_DIR)),
                    })
                time.sleep(1)   # be polite to a free public service

    if manifest_rows:
        manifest = OUT_DIR / "manifest.csv"
        write_header = not manifest.exists()
        with open(manifest, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(manifest_rows[0]))
            if write_header:
                w.writeheader()
            w.writerows(manifest_rows)
        print(f"\nManifest: {manifest}")

    print(f"\nDone. {total_files} DICOM files in {OUT_DIR}")
    print("\nNext: retrain per-modality models (Fix 6) —")
    print("  python train_isolation_forest.py --data datasets/training")
    return 0


if __name__ == "__main__":
    sys.exit(main())