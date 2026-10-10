from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str

    # Minimum 10 characters enforced here at the API boundary.
    #
    # bcrypt truncation note: bcrypt silently truncates passwords at 72 bytes.
    # A password of 72 identical characters is indistinguishable from one of
    # 73+.  For the threat model of this system (hospital SOC operators) the
    # 72-byte ceiling is not an operational concern, but it MUST NOT be
    # forgotten during future credential-handling changes.  If longer
    # passphrases are ever required, pre-hash with SHA-256 before bcrypt
    # (e.g. bcrypt(b64encode(sha256(password)), ...) — never truncate silently.
    password: str = Field(min_length=10)

    role: str = "viewer"


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class UploadResponse(BaseModel):
    message: str
    filename: str
    file_hash: str
    file_size: int


class AlertUpdateSchema(BaseModel):
    status: str = Field(..., description="New alert status: OPEN, RESOLVED, or IGNORED")


class AuditVerifyResponse(BaseModel):
    valid: bool
    entries_verified: int
    broken_at_id: int | None = None
    detail: str