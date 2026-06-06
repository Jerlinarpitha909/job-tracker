#!/usr/bin/env python3
"""
Standalone scheduler script.
Run directly: python scripts/run_reminders.py
Or add to cron: 0 9 * * * /usr/bin/python3 /path/to/scripts/run_reminders.py

Cron setup (daily at 9am):
  crontab -e
  Add: 0 9 * * * cd /path/to/job_tracker && python scripts/run_reminders.py >> logs/reminders.log 2>&1
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from job_tracker.automation import run_reminder_check

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "reminders.log"


def main():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = run_reminder_check()

    log_line = f"[{timestamp}] Checked: {result['checked']} | Flagged: {result['flagged']}"
    if result["flagged_jobs"]:
        log_line += " | Jobs: " + ", ".join(
            f"#{j['id']} {j['company']}" for j in result["flagged_jobs"]
        )

    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

    if result["flagged"] > 0:
        print(f"\n⚠  {result['flagged']} application(s) flagged as 'Follow Up Needed':")
        for j in result["flagged_jobs"]:
            print(f"   #{j['id']}  {j['company']} — {j['role']} ({j['days_since_applied']} days ago)")


if __name__ == "__main__":
    main()
