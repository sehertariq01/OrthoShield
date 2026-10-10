import os
from dotenv import load_dotenv

# Load .env file from the same directory as this config
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

SECRET_KEY = os.environ.get("ORTHOSHIELD_SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError(
        "ORTHOSHIELD_SECRET_KEY environment variable is not set. "
        "Add it to backend/.env before starting the server."
    )

ALGORITHM = "HS256"

# Role-based token lifetime (in minutes)
TOKEN_EXPIRY = {
    "admin":   8 * 60,   # 8 hours
    "analyst": 4 * 60,   # 4 hours
    "viewer":  1 * 60,   # 1 hour
}

# VirusTotal API key — used by virustotal_scan.py (hash lookups only, never file upload)
VT_API_KEY = os.environ.get("VT_API_KEY", "")

# Orthanc PACS Integration
ORTHANC_URL = os.environ.get("ORTHANC_URL", "http://localhost:9042").rstrip("/")
ORTHANC_USERNAME = os.environ.get("ORTHANC_USERNAME", "orthanc")
ORTHANC_PASSWORD = os.environ.get("ORTHANC_PASSWORD", "orthanc")