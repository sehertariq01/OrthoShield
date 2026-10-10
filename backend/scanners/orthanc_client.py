"""
Orthanc PACS Client
===================
Handles secure forwarding of verified CLEAN DICOM instances to the Orthanc PACS
REST API endpoint (POST /instances) using HTTP Basic Authentication.
"""
import logging
import requests
from config import ORTHANC_URL, ORTHANC_USERNAME, ORTHANC_PASSWORD

logger = logging.getLogger("orthoshield.orthanc")


def forward_to_orthanc(file_path: str) -> dict:
    """
    Forward a validated CLEAN DICOM file to Orthanc PACS.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the local DICOM file to forward.

    Returns
    -------
    dict
        {
            "success": bool,
            "instance_id": str | None,
            "status_code": int | None,
            "detail": str,
        }
    """
    if not ORTHANC_URL:
        msg = "Orthanc forwarding disabled: ORTHANC_URL not configured"
        logger.warning(msg)
        return {
            "success": False,
            "instance_id": None,
            "status_code": None,
            "detail": msg,
        }

    endpoint = f"{ORTHANC_URL}/instances"
    auth = (ORTHANC_USERNAME, ORTHANC_PASSWORD) if ORTHANC_USERNAME else None

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()

        response = requests.post(
            endpoint,
            data=file_data,
            headers={"Content-Type": "application/dicom"},
            auth=auth,
            timeout=30,
        )

        if response.status_code in (200, 201):
            try:
                data = response.json()
                instance_id = data.get("ID")
                status_desc = data.get("Status", "Success")
                detail = f"Instance {instance_id} stored in Orthanc ({status_desc})"
            except Exception:
                instance_id = None
                detail = f"Stored in Orthanc with HTTP {response.status_code}"

            logger.info("Forwarded %s to Orthanc -> %s", file_path, detail)
            return {
                "success": True,
                "instance_id": instance_id,
                "status_code": response.status_code,
                "detail": detail,
            }

        detail = f"Orthanc rejected instance (HTTP {response.status_code}): {response.text[:200]}"
        logger.error("Failed forwarding %s to Orthanc: %s", file_path, detail)
        return {
            "success": False,
            "instance_id": None,
            "status_code": response.status_code,
            "detail": detail,
        }

    except FileNotFoundError:
        detail = f"File not found on disk: {file_path}"
        logger.error("Orthanc forward error: %s", detail)
        return {
            "success": False,
            "instance_id": None,
            "status_code": None,
            "detail": detail,
        }
    except requests.RequestException as e:
        detail = f"Orthanc connection failed: {e}"
        logger.error("Orthanc forward network error: %s", detail)
        return {
            "success": False,
            "instance_id": None,
            "status_code": None,
            "detail": detail,
        }
    except Exception as e:
        detail = f"Unexpected error forwarding to Orthanc: {e}"
        logger.error(detail)
        return {
            "success": False,
            "instance_id": None,
            "status_code": None,
            "detail": detail,
        }
