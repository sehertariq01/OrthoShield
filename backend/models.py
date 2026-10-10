from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="viewer")
    ip_address = Column(String(45))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), nullable=False, index=True)
    filename = Column(String(255))
    risk_score = Column(Float, nullable=True)        # None when scan is incomplete
    decision = Column(String(20))                    # "CLEAN" or "BLOCKED"
    findings = Column(Text)                          # JSON string of check results
    uploaded_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Fix 3: quarantine path (set when decision == BLOCKED)
    quarantine_path = Column(String(500), nullable=True)
    # Fix 2: True when at least one scanner was unavailable during this scan
    incomplete_scan = Column(Boolean, default=False)



class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String(20))  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    status = Column(String(20), default="OPEN")  # "OPEN", "RESOLVED", "IGNORED"
    source = Column(String(50))  # e.g. "rule_check", "ml_model", "clamav"
    finding = Column(Text)
    scan_log_id = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event = Column(String(100), nullable=False)
    username = Column(String(100))
    details = Column(Text)
    previous_hash = Column(String(64))
    current_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String(255), unique=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    reason = Column(String(100))


class SHA256Store(Base):
    __tablename__ = "sha256_store"

    id = Column(Integer, primary_key=True, index=True)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)
    sop_instance_uid = Column(String(255))
    baseline_created_at = Column(DateTime(timezone=True), server_default=func.now())
