# 📋 Job Application Tracker

> A production-ready CLI tool to track, automate, and analyse your job hunt — built with Python OOP, SQLite, pytest, and openpyxl.

[![CI](https://github.com/Jerlinarpitha909/job-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/Jerlinarpitha909/job-tracker/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Add & track applications** | Store company, role, date, status, and notes in a local SQLite database via clean OOP models |
| 2 | **Auto-status reminders** | Flags applications with no update after 7 days as *"Follow Up Needed"* — runs on CLI trigger or cron schedule |
| 3 | **Analytics & export** | Stats dashboard (response rate, avg days to response) + CSV / Excel export |
| 4 | **Unit tests** | 40+ pytest tests covering models, CRUD, reminder logic, analytics, and edge cases |

---

## Project Structure

```
job_tracker/
├── job_tracker/
│   ├── __init__.py          # Public API
│   ├── models.py            # JobApplication dataclass + JobRepository (CRUD)
│   ├── automation.py        # Stale-application detection & flagging
│   ├── analytics.py         # Stats + CSV/Excel export
│   └── cli.py               # Full-featured CLI (argparse)
├── tests/
│   ├── conftest.py
│   └── test_tracker.py      # 40+ pytest tests
├── scripts/
│   ├── run_reminders.py     # Cron-ready reminder runner
│   └── seed_data.py         # Demo data seeder
├── exports/                 # Generated CSV/Excel files (git-ignored)
├── logs/                    # Reminder run logs (git-ignored)
├── .github/workflows/ci.yml # GitHub Actions CI
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/job-tracker.git
cd job-tracker

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### 2. Seed sample data (optional)

```bash
python scripts/seed_data.py
```

### 3. Run the CLI

```bash
# Add a new application (interactive prompt)
python -m job_tracker.cli add

# List all applications
python -m job_tracker.cli list

# Update status
python -m job_tracker.cli update 3 Interview

# Add notes
python -m job_tracker.cli notes 3 "Scheduled for panel interview next Tuesday"

# Search by keyword
python -m job_tracker.cli search Google

# Run reminder check (flags stale applications)
python -m job_tracker.cli remind

# View analytics dashboard
python -m job_tracker.cli stats

# Export to CSV
python -m job_tracker.cli export --format csv

# Export to Excel
python -m job_tracker.cli export --format excel

# Delete an application
python -m job_tracker.cli delete 5
```

---

## Status Flow

```
Applied → Interview → Offer
       ↘             ↘
        Rejected      Rejected
       ↓
  Follow Up Needed  (auto-flagged after 7 days of inactivity)
```

Valid statuses: `Applied`, `Interview`, `Offer`, `Rejected`, `Follow Up Needed`

---

## Automation & Scheduling

### CLI trigger
```bash
python -m job_tracker.cli remind
```

### Cron (daily at 9am)
```cron
0 9 * * * cd /path/to/job-tracker && python scripts/run_reminders.py >> logs/reminders.log 2>&1
```

---

## Analytics Dashboard

```
── Analytics Dashboard ──
  Total Applied        : 10
  Response Rate        : 40.0%
  Avg Days to Response : 12.5 days
  Oldest Open (days)   : 25

  By Status:
  Applied               3  ███
  Interview             2  ██
  Offer                 1  █
  Rejected              2  ██
  Follow Up Needed      2  ██
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=job_tracker --cov-report=term-missing

# Specific test class
pytest tests/test_tracker.py::TestAutomation -v
```

### Test Coverage Areas

| Module | Tests |
|--------|-------|
| `models.py` | Validation, CRUD, edge cases |
| `automation.py` | Stale detection, flagging, threshold logic |
| `analytics.py` | Stats calculation, CSV/Excel export |

---

## Architecture

```
CLI (cli.py)
    │
    ├── JobRepository (models.py)   ←──── SQLite (tracker.db)
    │       └── JobApplication (dataclass)
    │
    ├── Automation (automation.py)
    │       └── flag_stale_applications()
    │
    └── Analytics (analytics.py)
            ├── get_analytics()
            ├── export_to_csv()
            └── export_to_excel()
```

---

## License

MIT © 2025
