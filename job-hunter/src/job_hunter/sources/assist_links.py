"""LinkedIn / Naukri / Unstop do not offer public job-search APIs, and their
Terms of Service prohibit automated scraping and automated form submission
while logged in. Rather than build a bot that evades their anti-automation
detection (which risks your account being banned), this module builds
direct, pre-filled SEARCH links you open yourself in a normal browser.

For the actual application step, see `apply_assist.py` - a *local-only*
Playwright helper that opens the page in your own logged-in browser
profile and fills the visible fields for you, then stops and waits for
you to review and click submit. It is intentionally never wired into the
GitHub Actions workflow.
"""
from urllib.parse import quote_plus


def linkedin_search_url(keywords: str, location: str = "") -> str:
    q = quote_plus(keywords)
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}"
    if location:
        url += f"&location={quote_plus(location)}"
    return url


def naukri_search_url(keywords: str, location: str = "") -> str:
    q = quote_plus(keywords)
    slug = keywords.strip().lower().replace(" ", "-")
    url = f"https://www.naukri.com/{slug}-jobs"
    if location:
        url += f"-in-{quote_plus(location.lower().replace(' ', '-'))}"
    url += f"?k={q}"
    return url


def unstop_search_url(keywords: str) -> str:
    q = quote_plus(keywords)
    return f"https://unstop.com/jobs?searchTerm={q}"


def build_search_links(keywords: str, location: str = "") -> dict:
    return {
        "linkedin": linkedin_search_url(keywords, location),
        "naukri": naukri_search_url(keywords, location),
        "unstop": unstop_search_url(keywords),
    }
