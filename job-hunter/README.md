# Job Hunter Assistant

An automated job-hunting pipeline: it finds postings that match your resume,
tracks which ones you've applied to, watches your inbox for recruiter
replies, and pushes a daily report — twice a day, via GitHub Actions.

## What it actually automates (and what it doesn't)

Fully automated (no login, public/legitimate APIs, safe to run in CI):

- **RemoteOK, Greenhouse, Lever** job feeds — public JSON APIs.
- **Google Jobs** results — via [SerpApi](https://serpapi.com/google-jobs-api) (a paid proxy for Google Search results; avoids scraping Google directly).
- **Resume-to-posting skill matching** and ranking.
- **Gmail reply detection** — read-only OAuth, flags likely recruiter replies.
- **Daily report** — written to `reports/latest.md` and posted to a GitHub issue.

Deliberately **not** silently automated — **LinkedIn, Naukri, Unstop**:
these platforms have no public job-search API and their Terms of Service
prohibit scraping and automated form submission while logged in. Building a
bot that evades their anti-automation detection risks your account being
banned and isn't something this project does. Instead:

- The daily report includes **direct search links** for these sites so you
  can review matches yourself in one click.
- `apply_assist.py` is a **local-only** helper (never run in CI) that opens
  the job page in your own logged-in browser profile and pre-fills the
  obvious fields (name, email, phone, resume upload) — then stops and lets
  **you** review and click Submit. It never submits on your behalf.

## Project layout

```
job-hunter/
  src/job_hunter/
    resume_parser.py      # extract text + skills from your resume
    skills_taxonomy.py     # the list of skills it knows to look for
    matcher.py             # score postings against your resume's skills
    db.py                  # SQLite tracking of jobs/applications/replies
    email_tracker.py       # Gmail API reply detection
    report.py              # renders the daily markdown report
    apply_assist.py        # LOCAL ONLY semi-automated form-fill (Playwright)
    main.py                # orchestrator CLI, run daily by GitHub Actions
    sources/
      remoteok.py, greenhouse.py, lever.py, google_jobs.py
      assist_links.py      # LinkedIn/Naukri/Unstop search-link builder
  .github/workflows/daily-job-hunt.yml
  config.example.yaml
  tests/
```

## Setup

See [SETUP.md](./SETUP.md) for full step-by-step instructions (config,
resume, Gmail OAuth, GitHub secrets).

## Quick local run

```bash
cd job-hunter
pip install -r requirements.txt
cp config.example.yaml config.yaml   # then edit it
mkdir -p data && cp /path/to/your/resume.pdf data/resume.pdf
python -m job_hunter.main
cat reports/latest.md
```

## Tests

```bash
pip install pytest
pytest
```
