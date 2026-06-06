"""
Core ORM-style models for the Job Application Tracker.
Uses Python OOP classes backed by SQLite.
"""

import sqlite3
import csv
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

DB_PATH = Path(__file__).parent.parent / "tracker.db"

STATUS_FLOW = ["Applied", "Interview", "Offer", "Rejected", "Follow Up Needed"]


@dataclass
class JobApplication:
    company: str
    role: str
    status: str = "Applied"
    date_applied: str = field(default_factory=lambda: date.today().isoformat())
    notes: str = ""
    id: Optional[int] = None
    last_updated: Optional[str] = None

    def __post_init__(self):
        if self.status not in STATUS_FLOW:
            raise ValueError(f"Invalid status '{self.status}'. Choose from: {STATUS_FLOW}")
        if not self.company.strip():
            raise ValueError("Company name cannot be empty.")
        if not self.role.strip():
            raise ValueError("Role cannot be empty.")


class Database:
    """Manages SQLite connection and schema setup."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    company     TEXT    NOT NULL,
                    role        TEXT    NOT NULL,
                    status      TEXT    NOT NULL DEFAULT 'Applied',
                    date_applied TEXT   NOT NULL,
                    notes       TEXT    DEFAULT '',
                    last_updated TEXT   NOT NULL
                )
            """)
            conn.commit()


class JobRepository:
    """CRUD operations for job applications."""

    def __init__(self, db: Database = None):
        self.db = db or Database()

    def add(self, job: JobApplication) -> JobApplication:
        now = datetime.now().isoformat(timespec="seconds")
        with self.db.connect() as conn:
            cur = conn.execute(
                """INSERT INTO applications (company, role, status, date_applied, notes, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (job.company, job.role, job.status, job.date_applied, job.notes, now),
            )
            conn.commit()
            job.id = cur.lastrowid
            job.last_updated = now
        return job

    def get_all(self) -> list[JobApplication]:
        with self.db.connect() as conn:
            rows = conn.execute("SELECT * FROM applications ORDER BY date_applied DESC").fetchall()
        return [self._row_to_job(r) for r in rows]

    def get_by_id(self, job_id: int) -> Optional[JobApplication]:
        with self.db.connect() as conn:
            row = conn.execute("SELECT * FROM applications WHERE id = ?", (job_id,)).fetchone()
        return self._row_to_job(row) if row else None

    def update_status(self, job_id: int, new_status: str) -> bool:
        if new_status not in STATUS_FLOW:
            raise ValueError(f"Invalid status '{new_status}'. Choose from: {STATUS_FLOW}")
        now = datetime.now().isoformat(timespec="seconds")
        with self.db.connect() as conn:
            cur = conn.execute(
                "UPDATE applications SET status = ?, last_updated = ? WHERE id = ?",
                (new_status, now, job_id),
            )
            conn.commit()
        return cur.rowcount > 0

    def update_notes(self, job_id: int, notes: str) -> bool:
        now = datetime.now().isoformat(timespec="seconds")
        with self.db.connect() as conn:
            cur = conn.execute(
                "UPDATE applications SET notes = ?, last_updated = ? WHERE id = ?",
                (notes, now, job_id),
            )
            conn.commit()
        return cur.rowcount > 0

    def delete(self, job_id: int) -> bool:
        with self.db.connect() as conn:
            cur = conn.execute("DELETE FROM applications WHERE id = ?", (job_id,))
            conn.commit()
        return cur.rowcount > 0

    def search(self, keyword: str) -> list[JobApplication]:
        kw = f"%{keyword}%"
        with self.db.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM applications WHERE company LIKE ? OR role LIKE ? OR notes LIKE ?",
                (kw, kw, kw),
            ).fetchall()
        return [self._row_to_job(r) for r in rows]

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> JobApplication:
        return JobApplication(
            id=row["id"],
            company=row["company"],
            role=row["role"],
            status=row["status"],
            date_applied=row["date_applied"],
            notes=row["notes"],
            last_updated=row["last_updated"],
        )
