"""RemoteOK public JSON API - https://remoteok.com/api
No authentication required; this is RemoteOK's documented public feed."""
import requests

from .base import JobPosting

API_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "job-hunter-assistant/1.0 (personal job search tool)"}


def fetch(query_keywords: list[str] | None = None, limit: int = 50) -> list[JobPosting]:
    resp = requests.get(API_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    postings = []
    for item in data:
        if not isinstance(item, dict) or "id" not in item:
            continue  # first element is a legal notice, not a job

        title = item.get("position", "")
        description = item.get("description", "") or ""
        tags = item.get("tags", []) or []

        if query_keywords:
            haystack = f"{title} {description} {' '.join(tags)}".lower()
            if not any(kw.lower() in haystack for kw in query_keywords):
                continue

        postings.append(
            JobPosting(
                source="remoteok",
                external_id=str(item["id"]),
                title=title,
                company=item.get("company", ""),
                location=item.get("location", "Remote"),
                url=item.get("url", f"https://remoteok.com/remote-jobs/{item['id']}"),
                description=description,
                posted_at=item.get("date", ""),
                tags=tags,
            )
        )
        if len(postings) >= limit:
            break
    return postings
