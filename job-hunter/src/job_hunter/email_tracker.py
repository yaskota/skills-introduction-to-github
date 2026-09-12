"""Gmail reply detection via the official Gmail API (OAuth), read-only scope.

One-time setup (documented in SETUP.md) gets you a refresh token that is
then stored as a GitHub Actions secret (GMAIL_REFRESH_TOKEN) alongside your
OAuth client id/secret - no password is ever stored, and access is
read-only (gmail.readonly scope).

Each run searches for messages received since the last check that look
like replies to your job applications, using company-name / your-sent
addresses as heuristics, and records new ones so they aren't reported twice.
"""
from __future__ import annotations

import base64
import os
from email.utils import parseaddr

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

REPLY_KEYWORDS = [
    "your application", "application received", "thank you for applying",
    "interview", "next steps", "we regret", "unfortunately", "not moving forward",
    "shortlisted", "assessment", "offer", "schedule a call", "recruiter",
]


def get_gmail_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=creds)


def _get_header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def find_recent_replies(service, after_unix_ts: int, known_companies: list[str]) -> list[dict]:
    """Search Gmail for likely application-related replies received after
    the given timestamp. Returns a list of {message_id, from, subject, date}."""
    query = f"after:{after_unix_ts} category:primary"
    results = []
    page_token = None

    while True:
        resp = service.users().messages().list(
            userId="me", q=query, pageToken=page_token, maxResults=50
        ).execute()
        for msg_ref in resp.get("messages", []):
            msg = service.users().messages().get(
                userId="me", id=msg_ref["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            headers = msg["payload"]["headers"]
            subject = _get_header(headers, "Subject")
            from_addr = _get_header(headers, "From")
            snippet = msg.get("snippet", "")

            haystack = f"{subject} {snippet}".lower()
            company_hit = any(c.lower() in haystack or c.lower() in from_addr.lower()
                               for c in known_companies)
            keyword_hit = any(k in haystack for k in REPLY_KEYWORDS)

            if company_hit or keyword_hit:
                results.append({
                    "message_id": msg_ref["id"],
                    "from": parseaddr(from_addr)[1] or from_addr,
                    "subject": subject,
                    "date": _get_header(headers, "Date"),
                })

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return results
