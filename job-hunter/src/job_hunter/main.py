"""Orchestrator: fetch postings from all automated sources, match against
the resume, persist new matches/applications, check for email replies, and
write a daily report. Designed to be run twice a day by GitHub Actions
(morning + night) via `python -m job_hunter.main`."""
from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import yaml

from . import db
from .matcher import rank_postings
from .report import render_report
from .resume_parser import parse_resume
from .sources import greenhouse, lever, remoteok, google_jobs
from .sources.assist_links import build_search_links


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def gather_postings(config: dict) -> list:
    keywords = config.get("search_keywords", [])
    location = config.get("search_location", "")

    postings = []
    postings += remoteok.fetch(query_keywords=keywords)
    postings += greenhouse.fetch(config.get("greenhouse_boards", []), query_keywords=keywords)
    postings += lever.fetch(config.get("lever_companies", []), query_keywords=keywords)
    for kw in keywords:
        postings += google_jobs.fetch(kw, location=location)
    return postings


def check_replies(conn, config: dict, since_ts: int) -> list[dict]:
    required = ["GMAIL_REFRESH_TOKEN", "GMAIL_CLIENT_ID", "GMAIL_CLIENT_SECRET"]
    if not all(os.environ.get(v) for v in required):
        return []  # email tracking not configured yet

    from . import email_tracker

    service = email_tracker.get_gmail_service()
    known_companies = [row["company"] for row in
                        conn.execute("SELECT DISTINCT company FROM jobs WHERE status = 'applied'")]
    found = email_tracker.find_recent_replies(service, since_ts, known_companies)

    new_replies = []
    for item in found:
        inserted = db.record_reply(
            conn,
            job_dedupe_key=None,
            from_address=item["from"],
            subject=item["subject"],
            received_at=item["date"],
            gmail_message_id=item["message_id"],
        )
        if inserted:
            new_replies.append(item)
    return new_replies


def run(config_path: str, db_path: str, report_dir: str) -> str:
    config = load_config(config_path)
    since_iso = db.now()
    since_ts = int(time.time()) - 12 * 3600  # look back 12h (twice-daily cadence)

    resume = parse_resume(config["resume_path"])
    resume_skills = set(resume["skills"])

    postings = gather_postings(config)
    ranked = rank_postings(postings, resume_skills, min_score=config.get("min_match_score", 0.1))

    new_matches = []
    with db.connect(db_path) as conn:
        for r in ranked:
            p = r["posting"]
            is_new = db.upsert_job(
                conn, p.dedupe_key, p.source, p.title, p.company, p.location,
                p.url, r["score"], r["matched_skills"],
            )
            if is_new:
                new_matches.append(r)

        new_replies = check_replies(conn, config, since_ts)
        counts = db.counts_since(conn, since_iso)

    assist_links = build_search_links(
        config.get("search_keywords", [""])[0], config.get("search_location", "")
    )

    report_md = render_report(counts, new_matches, new_replies, assist_links)

    Path(report_dir).mkdir(parents=True, exist_ok=True)
    from datetime import datetime, timezone
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
    out_path = Path(report_dir) / f"report_{stamp}.md"
    out_path.write_text(report_md)

    latest_path = Path(report_dir) / "latest.md"
    latest_path.write_text(report_md)

    return report_md


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--db", default="job_hunter.db")
    parser.add_argument("--report-dir", default="reports")
    args = parser.parse_args()

    report_md = run(args.config, args.db, args.report_dir)
    print(report_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
