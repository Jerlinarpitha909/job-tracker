#!/usr/bin/env python3
"""
CLI for Job Application Tracker.
Usage:
  python -m job_tracker.cli add
  python -m job_tracker.cli list
  python -m job_tracker.cli update <id> <status>
  python -m job_tracker.cli notes <id> "<text>"
  python -m job_tracker.cli delete <id>
  python -m job_tracker.cli search <keyword>
  python -m job_tracker.cli remind
  python -m job_tracker.cli stats
  python -m job_tracker.cli export --format csv|excel
"""

import argparse
import json
import sys
from datetime import date

from job_tracker.models import JobApplication, JobRepository, STATUS_FLOW
from job_tracker.automation import run_reminder_check
from job_tracker.analytics import get_analytics, export_to_csv, export_to_excel

YELLOW = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

STATUS_COLORS = {
    "Applied":          CYAN,
    "Interview":        YELLOW,
    "Offer":            GREEN,
    "Rejected":         RED,
    "Follow Up Needed": "\033[35m",
}


def color_status(status: str) -> str:
    return f"{STATUS_COLORS.get(status, '')}{status}{RESET}"


def print_jobs(jobs):
    if not jobs:
        print(f"{YELLOW}No applications found.{RESET}")
        return
    print(f"\n{BOLD}{'ID':<5} {'Company':<22} {'Role':<28} {'Status':<22} {'Date Applied':<14} Notes{RESET}")
    print("─" * 105)
    for j in jobs:
        print(f"{j.id:<5} {j.company:<22} {j.role:<28} {color_status(j.status):<31} {j.date_applied:<14} {j.notes[:40]}")
    print()


def cmd_add(args):
    repo = JobRepository()
    print(f"\n{BOLD}── Add New Application ──{RESET}")
    company = input("Company: ").strip()
    role = input("Role: ").strip()
    notes = input("Notes (optional): ").strip()
    try:
        job = JobApplication(company=company, role=role, notes=notes)
        saved = repo.add(job)
        print(f"\n{GREEN}✔ Added [{saved.id}] {saved.company} — {saved.role}{RESET}")
    except ValueError as e:
        print(f"{RED}Error: {e}{RESET}")
        sys.exit(1)


def cmd_list(args):
    repo = JobRepository()
    jobs = repo.get_all()
    print(f"\n{BOLD}── All Applications ({len(jobs)}) ──{RESET}")
    print_jobs(jobs)


def cmd_update(args):
    repo = JobRepository()
    try:
        ok = repo.update_status(args.id, args.status)
        if ok:
            print(f"{GREEN}✔ Updated #{args.id} → {args.status}{RESET}")
        else:
            print(f"{RED}No application found with ID {args.id}{RESET}")
    except ValueError as e:
        print(f"{RED}{e}{RESET}")
        sys.exit(1)


def cmd_notes(args):
    repo = JobRepository()
    ok = repo.update_notes(args.id, args.text)
    if ok:
        print(f"{GREEN}✔ Notes updated for #{args.id}{RESET}")
    else:
        print(f"{RED}No application found with ID {args.id}{RESET}")


def cmd_delete(args):
    repo = JobRepository()
    confirm = input(f"Delete application #{args.id}? [y/N] ").strip().lower()
    if confirm == "y":
        ok = repo.delete(args.id)
        print(f"{GREEN}Deleted.{RESET}" if ok else f"{RED}Not found.{RESET}")


def cmd_search(args):
    repo = JobRepository()
    results = repo.search(args.keyword)
    print(f"\n{BOLD}── Search: '{args.keyword}' ({len(results)} results) ──{RESET}")
    print_jobs(results)


def cmd_remind(args):
    result = run_reminder_check()
    print(f"\n{BOLD}── Reminder Check ──{RESET}")
    print(f"Checked : {result['checked']} applications")
    print(f"Flagged : {result['flagged']} as 'Follow Up Needed'")
    if result["flagged_jobs"]:
        print(f"\n{YELLOW}Applications needing follow-up:{RESET}")
        for j in result["flagged_jobs"]:
            print(f"  #{j['id']} {j['company']} — {j['role']} ({j['days_since_applied']} days ago)")
    print()


def cmd_stats(args):
    a = get_analytics()
    print(f"\n{BOLD}── Analytics Dashboard ──{RESET}")
    print(f"  Total Applied        : {a['total_applied']}")
    print(f"  Response Rate        : {a['response_rate']}%")
    print(f"  Avg Days to Response : {a['avg_days_to_response']} days")
    print(f"  Oldest Open (days)   : {a['oldest_open']}")
    print(f"\n{BOLD}  By Status:{RESET}")
    for status, count in a["by_status"].items():
        bar = "█" * count
        print(f"  {color_status(status):<30}  {count:>3}  {bar}")
    print()


def cmd_export(args):
    repo = JobRepository()
    if args.format == "csv":
        path = export_to_csv(repo)
        print(f"{GREEN}✔ Exported to CSV: {path}{RESET}")
    elif args.format == "excel":
        path = export_to_excel(repo)
        print(f"{GREEN}✔ Exported to Excel: {path}{RESET}")
    else:
        print(f"{RED}Unknown format: {args.format}{RESET}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="job-tracker",
        description="Job Application Tracker CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("add", help="Add a new job application")
    sub.add_parser("list", help="List all applications")

    p_update = sub.add_parser("update", help="Update application status")
    p_update.add_argument("id", type=int, help="Application ID")
    p_update.add_argument("status", choices=STATUS_FLOW, help="New status")

    p_notes = sub.add_parser("notes", help="Update notes for an application")
    p_notes.add_argument("id", type=int, help="Application ID")
    p_notes.add_argument("text", help="New notes text")

    p_del = sub.add_parser("delete", help="Delete an application")
    p_del.add_argument("id", type=int, help="Application ID")

    p_search = sub.add_parser("search", help="Search applications")
    p_search.add_argument("keyword", help="Keyword to search")

    sub.add_parser("remind", help="Flag stale applications (>7 days)")
    sub.add_parser("stats", help="Show analytics dashboard")

    p_export = sub.add_parser("export", help="Export to CSV or Excel")
    p_export.add_argument("--format", choices=["csv", "excel"], default="csv")

    args = parser.parse_args()
    handlers = {
        "add":    cmd_add,
        "list":   cmd_list,
        "update": cmd_update,
        "notes":  cmd_notes,
        "delete": cmd_delete,
        "search": cmd_search,
        "remind": cmd_remind,
        "stats":  cmd_stats,
        "export": cmd_export,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
