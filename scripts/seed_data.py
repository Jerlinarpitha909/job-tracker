#!/usr/bin/env python3
"""
Seeds the database with realistic sample data for demos and testing.
Usage: python scripts/seed_data.py
"""

import sys
from pathlib import Path
from datetime import date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from job_tracker.models import JobApplication, JobRepository, Database

SAMPLE_JOBS = [
    {"company": "Google",       "role": "Senior Software Engineer",   "status": "Interview",        "days_ago": 14, "notes": "L5 role, 4 rounds total"},
    {"company": "Stripe",       "role": "Backend Engineer",           "status": "Applied",          "days_ago": 3,  "notes": "Applied via referral"},
    {"company": "Volvo Cars",   "role": "Embedded Systems Engineer",  "status": "Offer",            "days_ago": 30, "notes": "SEK 780k + relocation"},
    {"company": "Spotify",      "role": "Platform Engineer",          "status": "Rejected",         "days_ago": 20, "notes": "Failed system design round"},
    {"company": "Klarna",       "role": "Software Engineer II",       "status": "Applied",          "days_ago": 10, "notes": "Stockholm HQ"},
    {"company": "Anthropic",    "role": "ML Infrastructure Engineer", "status": "Interview",        "days_ago": 5,  "notes": "Exciting! Distributed systems focus"},
    {"company": "IKEA Tech",    "role": "Backend Developer",          "status": "Applied",          "days_ago": 18, "notes": "Via LinkedIn"},
    {"company": "King",         "role": "Senior Developer",           "status": "Follow Up Needed", "days_ago": 25, "notes": "No reply after first screen"},
    {"company": "Ericsson",     "role": "5G Software Engineer",       "status": "Applied",          "days_ago": 2,  "notes": ""},
    {"company": "H&M Group",    "role": "Cloud Platform Engineer",    "status": "Rejected",         "days_ago": 40, "notes": "Culture fit concerns"},
]


def seed():
    repo = JobRepository()
    for data in SAMPLE_JOBS:
        applied_date = (date.today() - timedelta(days=data["days_ago"])).isoformat()
        job = JobApplication(
            company=data["company"],
            role=data["role"],
            status=data["status"],
            date_applied=applied_date,
            notes=data["notes"],
        )
        saved = repo.add(job)
        print(f"  [{saved.id:>2}] {saved.company:<20} {saved.role:<35} {saved.status}")

    print(f"\n✔ Seeded {len(SAMPLE_JOBS)} applications.")


if __name__ == "__main__":
    print("Seeding database with sample data...\n")
    seed()
