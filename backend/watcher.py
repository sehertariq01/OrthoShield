"""
OrthoShield Orthanc Watcher Service
===================================
Standalone surveillance daemon that polls Orthanc PACS's changes feed
(GET /changes) every 5 seconds to monitor, detect, and log all newly stored
DICOM instances and clinical events in real time.

Usage:
    python backend/watcher.py
    # or from backend/: python watcher.py
"""
import os
import sys
import time
import signal
import logging
from pathlib import Path

# Add backend directory to sys.path so config can be imported directly
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from config import ORTHANC_URL, ORTHANC_USERNAME, ORTHANC_PASSWORD
import requests

# ── Logging Setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [WATCHER] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("orthoshield.watcher")

RUNNING = True


def handle_sigint(signum, frame):
    global RUNNING
    logger.info("Shutdown signal received. Stopping Orthanc Watcher gracefully...")
    RUNNING = False


signal.signal(signal.SIGINT, handle_sigint)
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, handle_sigint)


def fetch_instance_summary(instance_id: str, auth: tuple | None) -> str:
    """
    Fetch basic technical metadata for a newly observed DICOM instance.
    PatientName is omitted to prevent PHI exposure in persistent log files.
    """
    url = f"{ORTHANC_URL}/instances/{instance_id}/simplified-tags"
    try:
        r = requests.get(url, auth=auth, timeout=5)
        if r.status_code == 200:
            tags = r.json()
            modality = tags.get("Modality", "Unknown")
            sop_uid = tags.get("SOPInstanceUID", "Unknown")
            return f"Modality={modality}, SOPInstanceUID={sop_uid}"
    except Exception:
        pass
    return f"InstanceID={instance_id}"



def run_watcher(poll_interval: float = 5.0):
    """Poll Orthanc /changes feed indefinitely and log new instance events."""
    global RUNNING

    auth = (ORTHANC_USERNAME, ORTHANC_PASSWORD) if ORTHANC_USERNAME else None
    changes_url = f"{ORTHANC_URL}/changes"

    logger.info("Starting Orthanc Watcher Service...")
    logger.info("Target Orthanc URL: %s", ORTHANC_URL)
    logger.info("Polling Interval: %.1f seconds", poll_interval)

    # Discover current latest change sequence so we only process new events
    last_change_id = 0
    try:
        r = requests.get(f"{changes_url}?last", auth=auth, timeout=10)
        if r.status_code == 200:
            last_change_id = r.json().get("Last", 0)
            logger.info("Connected to Orthanc. Starting from change sequence ID: %d", last_change_id)
        else:
            logger.warning("Could not get initial change seq (HTTP %d). Starting from 0.", r.status_code)
    except requests.RequestException as e:
        logger.warning("Initial connection to Orthanc failed: %e. Will retry in loop...", e)

    while RUNNING:
        try:
            params = {"since": last_change_id, "limit": 100}
            response = requests.get(changes_url, params=params, auth=auth, timeout=10)

            if response.status_code == 200:
                data = response.json()
                changes = data.get("Changes", [])
                last_change_id = data.get("Last", last_change_id)

                for change in changes:
                    change_type = change.get("ChangeType")
                    seq = change.get("Seq")
                    resource_id = change.get("ID")
                    path = change.get("Path")

                    if change_type == "NewInstance" or change_type == 5:
                        summary = fetch_instance_summary(resource_id, auth)
                        logger.info(
                            "NEW INSTANCE STORED [Seq=%d]: ID=%s | %s | Path=%s",
                            seq, resource_id, summary, path
                        )
                    elif change_type == "NewStudy" or change_type == 2:
                        logger.info("NEW STUDY CREATED [Seq=%d]: StudyID=%s", seq, resource_id)
                    elif change_type == "NewPatient" or change_type == 0:
                        logger.info("NEW PATIENT REGISTERED [Seq=%d]: PatientID=%s", seq, resource_id)
                    elif change_type == "Deleted":
                        logger.info("RESOURCE DELETED [Seq=%d]: ID=%s", seq, resource_id)

            elif response.status_code == 401:
                logger.error("Authentication failed against Orthanc (HTTP 401). Check credentials.")
            else:
                logger.warning("Orthanc /changes returned HTTP %d: %s", response.status_code, response.text[:100])

        except requests.RequestException as e:
            logger.warning("Connection to Orthanc unavailable: %s", e)
        except Exception as e:
            logger.error("Unexpected watcher error: %s", e)

        # Sleep in small increments to respond quickly to SIGINT
        elapsed = 0.0
        while elapsed < poll_interval and RUNNING:
            time.sleep(0.5)
            elapsed += 0.5

    logger.info("Orthanc Watcher Service stopped.")


if __name__ == "__main__":
    run_watcher()
