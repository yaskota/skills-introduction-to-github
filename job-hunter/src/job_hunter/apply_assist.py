"""LOCAL-ONLY semi-automated application assistant.

This script is NOT run by the GitHub Actions workflow and never will be -
it needs your real, logged-in browser session, which CI does not have and
should not have.

What it does:
  1. Launches Chromium using YOUR persistent browser profile (so you're
     already logged into LinkedIn/Naukri/Unstop, same as normal browsing).
  2. Navigates to a job URL you give it.
  3. Fills in the obvious text fields it can find (name, email, phone,
     resume upload) from your profile config.
  4. Stops. It does NOT click Apply/Submit. You review the filled form and
     submit it yourself.

This keeps you in full control and in compliance with each site's terms,
while removing the tedious retyping-your-details-every-time part.

Usage:
    python -m job_hunter.apply_assist --url "<job posting url>" --profile config.yaml
"""
from __future__ import annotations

import argparse
import sys

import yaml


def fill_form(page, profile: dict) -> None:
    """Best-effort fill of common application-form fields. Sites change
    their markup often, so this uses loose, label-based heuristics and
    silently skips fields it can't confidently find."""
    field_map = {
        "name": profile.get("full_name", ""),
        "first name": profile.get("first_name", ""),
        "last name": profile.get("last_name", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "linkedin": profile.get("linkedin_url", ""),
        "portfolio": profile.get("portfolio_url", ""),
    }

    for label_text, value in field_map.items():
        if not value:
            continue
        try:
            locator = page.get_by_label(label_text, exact=False)
            if locator.count() > 0:
                locator.first.fill(value)
        except Exception:
            continue

    resume_path = profile.get("resume_path")
    if resume_path:
        try:
            file_input = page.locator("input[type='file']").first
            if file_input.count() > 0:
                file_input.set_input_files(resume_path)
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True, help="Job posting / application URL")
    parser.add_argument("--profile", default="config.yaml", help="Path to config.yaml")
    parser.add_argument(
        "--user-data-dir",
        default="./.browser-profile",
        help="Persistent Chromium profile dir (log in here once, reused every run)",
    )
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Playwright is not installed. Run:\n"
            "  pip install playwright\n"
            "  playwright install chromium\n"
            "This tool is local-only and intentionally not in requirements.txt "
            "(it's never used in the automated CI pipeline).",
            file=sys.stderr,
        )
        return 1

    with open(args.profile) as f:
        config = yaml.safe_load(f)
    profile = config.get("applicant_profile", {})

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            args.user_data_dir, headless=False
        )
        page = context.new_page()
        page.goto(args.url, wait_until="domcontentloaded")

        print("Loaded page. Attempting best-effort field fill...")
        fill_form(page, profile)

        print(
            "\nDone pre-filling what could be matched automatically.\n"
            "Please REVIEW the form yourself, fix anything wrong, attach\n"
            "any additional documents, and click Submit/Apply manually.\n"
            "This tool will never click Submit for you.\n"
        )
        input("Press Enter here once you're done (this keeps the browser open)... ")
        context.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
