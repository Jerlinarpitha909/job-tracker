"""
Automation: flags stale applications and handles scheduled reminder checks.
"""

from datetime import datetime, date, timedelta
from job_tracker.models import JobRepository, JobApplication

FOLLOW_UP_DAYS = 7
STALE_STATUSES = {"Applied", "Interview"}


def flag_stale_applications(repo: JobRepository = None, threshold_days: int = FOLLOW_UP_DAYS) -> list[JobApplication]:
    """
    Checks all open applications. If last_updated > threshold_days ago
    and status is still 'Applied' or 'Interview', mark as 'Follow Up Needed'.
    Returns the list of flagged applications.
    """
    repo = repo or JobRepository()
    cutoff = datetime.now() - timedelta(days=threshold_days)
    flagged = []

    for job in repo.get_all():
        if job.status not in STALE_STATUSES:
            continue
        try:
            last = datetime.fromisoformat(job.last_updated)
        except (TypeError, ValueError):
            continue
        if last < cutoff:
            repo.update_status(job.id, "Follow Up Needed")
            job.status = "Follow Up Needed"
            flagged.append(job)

    return flagged


def days_since_applied(job: JobApplication) -> int:
    """Returns the number of days since the job was applied to."""
    try:
        applied = date.fromisoformat(job.date_applied)
        return (date.today() - applied).days
    except (TypeError, ValueError):
        return -1


def is_stale(job: JobApplication, threshold_days: int = FOLLOW_UP_DAYS) -> bool:
    """Returns True if a job has had no update in threshold_days."""
    if job.status not in STALE_STATUSES:
        return False
    try:
        last = datetime.fromisoformat(job.last_updated)
        return (datetime.now() - last).days >= threshold_days
    except (TypeError, ValueError):
        return False


def run_reminder_check(repo: JobRepository = None) -> dict:
    """
    Entry point for CLI / scheduled trigger.
    Flags stale applications and returns a summary dict.
    """
    repo = repo or JobRepository()
    flagged = flag_stale_applications(repo)
    all_jobs = repo.get_all()

    return {
        "checked": len(all_jobs),
        "flagged": len(flagged),
        "flagged_jobs": [
            {"id": j.id, "company": j.company, "role": j.role, "days_since_applied": days_since_applied(j)}
            for j in flagged
        ],
    }
