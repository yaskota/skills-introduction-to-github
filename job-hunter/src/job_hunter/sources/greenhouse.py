"""Greenhouse public job-board API. Any company using Greenhouse exposes
a public, unauthenticated JSON feed at this URL - this is documented and
intended for consumption (it's what powers their own careers pages).

Configure which companies to check in config.yaml under `greenhouse_boards`,
using the board token from their careers URL:
  https://boards.greenhouse.io/<board_token>
"""
import requests

from .base import JobPosting

API_URL = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"


def fetch(board_tokens: list[str], query_keywords: list[str] | None = None) -> list[JobPosting]:
    postings = []
    for board in board_tokens:
        try:
            resp = requests.get(API_URL.format(board=board), timeout=20)
            resp.raise_for_status()
        except requests.RequestException:
            continue

        for job in resp.json().get("jobs", []):
            title = job.get("title", "")
            content = job.get("content", "") or ""

            if query_keywords:
                haystack = f"{title} {content}".lower()
                if not any(kw.lower() in haystack for kw in query_keywords):
                    continue

            location = (job.get("location") or {}).get("name", "")
            postings.append(
                JobPosting(
                    source="greenhouse",
                    external_id=str(job["id"]),
                    title=title,
                    company=board,
                    location=location,
                    url=job.get("absolute_url", ""),
                    description=content,
                    posted_at=job.get("updated_at", ""),
                )
            )
    return postings
