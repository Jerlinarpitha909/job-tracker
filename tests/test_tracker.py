"""
Pytest test suite for Job Application Tracker.
Covers: models, CRUD, automation logic, analytics, and edge cases.
"""

import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from job_tracker.models import JobApplication, JobRepository, Database, STATUS_FLOW
from job_tracker.automation import flag_stale_applications, is_stale, days_since_applied, run_reminder_check
from job_tracker.analytics import get_analytics, export_to_csv, export_to_excel


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    """Provides a fresh Database backed by a temp file."""
    return Database(db_path=tmp_path / "test.db")


@pytest.fixture
def repo(tmp_db):
    """Provides a JobRepository with a fresh temp database."""
    return JobRepository(db=tmp_db)


@pytest.fixture
def sample_job():
    return JobApplication(company="Acme Corp", role="Software Engineer", notes="Referral from John")


@pytest.fixture
def repo_with_data(repo):
    """Repo pre-loaded with 3 jobs in different statuses."""
    repo.add(JobApplication(company="Google", role="SRE", status="Applied"))
    repo.add(JobApplication(company="Meta", role="Backend Engineer", status="Interview"))
    repo.add(JobApplication(company="Startup X", role="CTO", status="Rejected"))
    return repo


# ─── JobApplication model validation ─────────────────────────────────────────

class TestJobApplicationModel:
    def test_valid_creation(self, sample_job):
        assert sample_job.company == "Acme Corp"
        assert sample_job.role == "Software Engineer"
        assert sample_job.status == "Applied"

    def test_default_status_is_applied(self):
        job = JobApplication(company="X", role="Y")
        assert job.status == "Applied"

    def test_invalid_status_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            JobApplication(company="X", role="Y", status="Ghosted")

    def test_empty_company_raises(self):
        with pytest.raises(ValueError, match="Company name cannot be empty"):
            JobApplication(company="  ", role="Engineer")

    def test_empty_role_raises(self):
        with pytest.raises(ValueError, match="Role cannot be empty"):
            JobApplication(company="Acme", role="")

    def test_all_valid_statuses(self):
        for status in STATUS_FLOW:
            job = JobApplication(company="X", role="Y", status=status)
            assert job.status == status


# ─── CRUD Operations ──────────────────────────────────────────────────────────

class TestJobRepository:
    def test_add_returns_job_with_id(self, repo, sample_job):
        saved = repo.add(sample_job)
        assert saved.id is not None
        assert saved.id > 0

    def test_add_and_get_all(self, repo, sample_job):
        repo.add(sample_job)
        jobs = repo.get_all()
        assert len(jobs) == 1
        assert jobs[0].company == "Acme Corp"

    def test_get_by_id(self, repo, sample_job):
        saved = repo.add(sample_job)
        fetched = repo.get_by_id(saved.id)
        assert fetched is not None
        assert fetched.role == "Software Engineer"

    def test_get_by_id_missing_returns_none(self, repo):
        assert repo.get_by_id(9999) is None

    def test_update_status_valid(self, repo, sample_job):
        saved = repo.add(sample_job)
        result = repo.update_status(saved.id, "Interview")
        assert result is True
        assert repo.get_by_id(saved.id).status == "Interview"

    def test_update_status_invalid_raises(self, repo, sample_job):
        saved = repo.add(sample_job)
        with pytest.raises(ValueError):
            repo.update_status(saved.id, "Ghosted")

    def test_update_status_nonexistent_returns_false(self, repo):
        assert repo.update_status(9999, "Rejected") is False

    def test_update_notes(self, repo, sample_job):
        saved = repo.add(sample_job)
        repo.update_notes(saved.id, "Updated note")
        assert repo.get_by_id(saved.id).notes == "Updated note"

    def test_delete_job(self, repo, sample_job):
        saved = repo.add(sample_job)
        assert repo.delete(saved.id) is True
        assert repo.get_by_id(saved.id) is None

    def test_delete_nonexistent_returns_false(self, repo):
        assert repo.delete(9999) is False

    def test_search_by_company(self, repo_with_data):
        results = repo_with_data.search("Google")
        assert len(results) == 1
        assert results[0].company == "Google"

    def test_search_by_role(self, repo_with_data):
        results = repo_with_data.search("Backend")
        assert len(results) == 1
        assert results[0].role == "Backend Engineer"

    def test_search_no_results(self, repo_with_data):
        assert repo_with_data.search("Nintendo") == []

    def test_multiple_jobs_stored_independently(self, repo):
        repo.add(JobApplication(company="A", role="Dev"))
        repo.add(JobApplication(company="B", role="QA"))
        repo.add(JobApplication(company="C", role="PM"))
        assert len(repo.get_all()) == 3

    def test_last_updated_set_on_add(self, repo, sample_job):
        saved = repo.add(sample_job)
        assert saved.last_updated is not None

    def test_last_updated_changes_on_status_update(self, repo, sample_job):
        saved = repo.add(sample_job)
        original_ts = repo.get_by_id(saved.id).last_updated
        repo.update_status(saved.id, "Interview")
        new_ts = repo.get_by_id(saved.id).last_updated
        assert new_ts >= original_ts


# ─── Automation / Reminder Logic ─────────────────────────────────────────────

class TestAutomation:
    def _make_stale_job(self, repo, days_ago=10, status="Applied"):
        """Helper: adds a job and manually backdates its last_updated."""
        job = repo.add(JobApplication(company="OldCo", role="Dev", status=status))
        stale_ts = (datetime.now() - timedelta(days=days_ago)).isoformat(timespec="seconds")
        with repo.db.connect() as conn:
            conn.execute(
                "UPDATE applications SET last_updated = ? WHERE id = ?",
                (stale_ts, job.id),
            )
            conn.commit()
        return repo.get_by_id(job.id)

    def test_flag_stale_applications_flags_old_applied(self, repo):
        self._make_stale_job(repo, days_ago=10, status="Applied")
        flagged = flag_stale_applications(repo, threshold_days=7)
        assert len(flagged) == 1
        assert flagged[0].status == "Follow Up Needed"

    def test_flag_stale_does_not_flag_recent(self, repo):
        repo.add(JobApplication(company="NewCo", role="Dev", status="Applied"))
        flagged = flag_stale_applications(repo, threshold_days=7)
        assert len(flagged) == 0

    def test_flag_stale_ignores_rejected(self, repo):
        self._make_stale_job(repo, days_ago=10, status="Rejected")
        flagged = flag_stale_applications(repo, threshold_days=7)
        assert len(flagged) == 0

    def test_flag_stale_ignores_offer(self, repo):
        self._make_stale_job(repo, days_ago=10, status="Offer")
        flagged = flag_stale_applications(repo, threshold_days=7)
        assert len(flagged) == 0

    def test_flag_stale_flags_interview(self, repo):
        self._make_stale_job(repo, days_ago=15, status="Interview")
        flagged = flag_stale_applications(repo, threshold_days=7)
        assert len(flagged) == 1

    def test_is_stale_true_for_old_applied(self, repo):
        job = self._make_stale_job(repo, days_ago=10)
        assert is_stale(job, threshold_days=7) is True

    def test_is_stale_false_for_recent(self, repo):
        job = repo.add(JobApplication(company="X", role="Y", status="Applied"))
        assert is_stale(job, threshold_days=7) is False

    def test_is_stale_false_for_terminal_status(self, repo):
        job = self._make_stale_job(repo, days_ago=30, status="Rejected")
        assert is_stale(job, threshold_days=7) is False

    def test_days_since_applied(self):
        from datetime import date
        job = JobApplication(company="X", role="Y", date_applied=date.today().isoformat())
        assert days_since_applied(job) == 0

    def test_days_since_applied_past(self):
        past = (datetime.now() - timedelta(days=5)).date().isoformat()
        job = JobApplication(company="X", role="Y", date_applied=past)
        assert days_since_applied(job) == 5

    def test_run_reminder_check_returns_dict(self, repo):
        result = run_reminder_check(repo)
        assert "checked" in result
        assert "flagged" in result
        assert "flagged_jobs" in result

    def test_run_reminder_check_counts_correctly(self, repo):
        self._make_stale_job(repo, days_ago=10, status="Applied")
        repo.add(JobApplication(company="NewCo", role="Dev"))
        result = run_reminder_check(repo)
        assert result["checked"] == 2
        assert result["flagged"] == 1


# ─── Analytics ────────────────────────────────────────────────────────────────

class TestAnalytics:
    def test_empty_db_returns_zeros(self, repo):
        a = get_analytics(repo)
        assert a["total_applied"] == 0
        assert a["response_rate"] == 0.0

    def test_total_applied_count(self, repo_with_data):
        a = get_analytics(repo_with_data)
        assert a["total_applied"] == 3

    def test_by_status_keys(self, repo_with_data):
        a = get_analytics(repo_with_data)
        assert "Applied" in a["by_status"]
        assert "Interview" in a["by_status"]
        assert "Rejected" in a["by_status"]

    def test_response_rate_calculation(self, repo):
        repo.add(JobApplication(company="A", role="Dev", status="Applied"))
        repo.add(JobApplication(company="B", role="Dev", status="Interview"))
        repo.add(JobApplication(company="C", role="Dev", status="Offer"))
        a = get_analytics(repo)
        # 2 out of 3 progressed
        assert a["response_rate"] == pytest.approx(66.7, abs=0.1)

    def test_export_to_csv_creates_file(self, repo_with_data, tmp_path):
        path = export_to_csv(repo_with_data, filepath=tmp_path / "out.csv")
        assert path.exists()
        content = path.read_text()
        assert "company" in content.lower()
        assert "Google" in content

    def test_export_to_csv_correct_row_count(self, repo_with_data, tmp_path):
        import csv
        path = export_to_csv(repo_with_data, filepath=tmp_path / "out.csv")
        with open(path) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 3

    def test_export_to_excel_creates_file(self, repo_with_data, tmp_path):
        pytest.importorskip("openpyxl")
        path = export_to_excel(repo_with_data, filepath=tmp_path / "out.xlsx")
        assert path.exists()
        assert path.stat().st_size > 0
