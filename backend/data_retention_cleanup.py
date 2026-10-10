"""
Data Retention Cleanup Script
==============================
Deletes scan_log records older than RETENTION_DAYS (default: 90 days).

Run manually when needed:
    python data_retention_cleanup.py

Or schedule via Windows Task Scheduler / cron for automatic cleanup.

Note: Linked alerts are NOT automatically deleted — review and resolve them
before running this script to avoid orphaned alert records.
"""

from datetime import datetime, timedelta, timezone
from database import SessionLocal
import models

# ── Configuration ──────────────────────────────────────────────────────────
RETENTION_DAYS = 90  # scan_log records older than this will be deleted


def cleanup_old_records() -> None:
    db = SessionLocal()

    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)

        # Count before deletion
        old_logs = db.query(models.ScanLog).filter(
            models.ScanLog.created_at < cutoff_date
        ).all()

        print(f"[Data Retention] Cutoff date : {cutoff_date.strftime('%Y-%m-%d')}")
        print(f"[Data Retention] Found       : {len(old_logs)} scan_log record(s) older than {RETENTION_DAYS} days")

        if not old_logs:
            print("[Data Retention] Nothing to delete. Exiting.")
            return

        for log in old_logs:
            print(f"  - Deleting scan_log id={log.id}  file={log.filename}  date={log.created_at}")
            db.delete(log)

        db.commit()
        print(f"[Data Retention] Cleanup complete. {len(old_logs)} record(s) deleted.")

    except Exception as e:
        db.rollback()
        print(f"[Data Retention] ERROR: {str(e)}")

    finally:
        db.close()


if __name__ == "__main__":
    cleanup_old_records()
