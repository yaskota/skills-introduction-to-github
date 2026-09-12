"""Lever public postings API - also documented/public, no auth needed.
Configure company slugs (from https://jobs.lever.co/<slug>) in
config.yaml under `lever_companies`."""
import requests

from .base import JobPosting, keyword_matches

API_URL = "https://api.lever.co/v0/postings/{company}?mode=json"


def fetch(companies: list[str], query_keywords: list[str] | None = None) -> list[JobPosting]:
    postings = []
    for company in companies:
        try:
            resp = requests.get(API_URL.format(company=company), timeout=20)
            resp.raise_for_status()
        except requests.RequestException:
            continue

        for job in resp.json():
            title = job.get("text", "")
            description = job.get("descriptionPlain", "") or job.get("description", "") or ""

            if query_keywords:
                haystack = f"{title} {description}"
                if not keyword_matches(query_keywords, haystack):
                    continue

            categories = job.get("categories", {}) or {}
            postings.append(
                JobPosting(
                    source="lever",
                    external_id=str(job.get("id")),
                    title=title,
                    company=company,
                    location=categories.get("location", ""),
                    url=job.get("hostedUrl", ""),
                    description=description,
                    posted_at=str(job.get("createdAt", "")),
                )
            )
    return postings
