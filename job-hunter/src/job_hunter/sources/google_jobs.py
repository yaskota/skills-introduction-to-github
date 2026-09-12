"""Google Jobs results via SerpApi (https://serpapi.com/google-jobs-api).

Google itself has no public job-search API; SerpApi is a paid third-party
service that legitimately proxies Google's search results (this avoids
scraping Google directly, which its ToS prohibits). Requires a SERPAPI_KEY.
If no key is configured, this source is silently skipped.
"""
import os

import requests

from .base import JobPosting

API_URL = "https://serpapi.com/search.json"


def fetch(query: str, location: str = "", limit: int = 20) -> list[JobPosting]:
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return []

    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": api_key,
    }
    resp = requests.get(API_URL, params=params, timeout=20)
    resp.raise_for_status()
    results = resp.json().get("jobs_results", [])

    postings = []
    for job in results[:limit]:
        apply_options = job.get("apply_options") or []
        url = apply_options[0]["link"] if apply_options else job.get("share_link", "")
        postings.append(
            JobPosting(
                source="google_jobs",
                external_id=job.get("job_id", job.get("title", "")),
                title=job.get("title", ""),
                company=job.get("company_name", ""),
                location=job.get("location", ""),
                url=url,
                description=job.get("description", ""),
                posted_at=(job.get("detected_extensions") or {}).get("posted_at", ""),
            )
        )
    return postings
