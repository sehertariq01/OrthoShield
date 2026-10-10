# OrthoShield API Contract — /upload Endpoint

## Request
POST /upload
Headers: Authorization: Bearer <JWT>
Body: multipart/form-data, field name "file"

## Response (200 OK)
```json
{
  "message": "File uploaded successfully",
  "filename": "string",
  "file_hash": "string (SHA-256 hex)",
  "file_size": "integer (bytes)",
  "metadata": {
    "is_valid_dicom": "boolean",
    "sop_instance_uid": "string",
    "modality": "string",
    "rows": "integer",
    "columns": "integer",
    "study_date": "string (YYYYMMDD)",
    "...": "additional DICOM metadata fields"
  },
  "rule_checks": [
    {
      "check": "string (check name)",
      "passed": "boolean",
      "reason": "string (human-readable explanation)"
    }
  ],
  "risk_score": "float (0-100)",
  "decision": "string (CLEAN | BLOCKED)",
  "failed_checks_summary": [
    {
      "check": "string",
      "weight": "integer",
      "reason": "string"
    }
  ]
}
```

## Decision Values
- `CLEAN` — file passed inspection; should be forwarded to Orthanc
- `BLOCKED` — file failed inspection; alert created, not forwarded

## Other Endpoints
- POST /login → { access_token, token_type, role }
- GET /me → { username, role }
- POST /users → create user (dev-only currently)