# Setup Guide

## 1. Configure your search

```bash
cd job-hunter
cp config.example.yaml config.yaml
```

Edit `config.yaml`:
- `resume_path` — path to your resume (kept local, not committed).
- `search_keywords` — job titles/skills to search for.
- `search_location` — for Google Jobs and the Naukri/LinkedIn link builder.
- `greenhouse_boards` / `lever_companies` — optional, add company board
  tokens (from `boards.greenhouse.io/<token>` or `jobs.lever.co/<slug>`)
  for companies you specifically want to watch.
- `applicant_profile` — used only by the local `apply_assist.py` tool.

Put your resume at the path you configured, e.g. `data/resume.pdf`
(`.pdf`, `.docx` and `.txt` are supported).

## 2. (Optional) Google Jobs via SerpApi

Sign up at https://serpapi.com, get an API key, and either:
- export it locally as `SERPAPI_KEY`, or
- add it as a GitHub Actions secret named `SERPAPI_KEY`.

If you skip this, Google Jobs results are simply omitted — everything else
still works.

## 3. (Optional but recommended) Gmail reply detection

This uses OAuth with the read-only `gmail.readonly` scope — it can never
send, delete, or modify your email.

1. Go to https://console.cloud.google.com, create a project, enable the
   **Gmail API**.
2. Configure the OAuth consent screen (External, Testing mode is fine for
   personal use) and create an **OAuth client ID** of type "Desktop app".
   Note the Client ID and Client Secret.
3. Run this once on your own machine to get a refresh token:

```bash
pip install google-auth-oauthlib
python - <<'EOF'
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    },
    scopes=["https://www.googleapis.com/auth/gmail.readonly"],
)
creds = flow.run_local_server(port=0)
print("Refresh token:", creds.refresh_token)
EOF
```

4. Save the three values as GitHub repository secrets (Settings → Secrets
   and variables → Actions → Secrets):
   - `GMAIL_CLIENT_ID`
   - `GMAIL_CLIENT_SECRET`
   - `GMAIL_REFRESH_TOKEN`

## 4. GitHub Actions setup (the daily morning/night run)

1. Add a **repository variable** (Settings → Secrets and variables →
   Actions → Variables) named `JOB_HUNTER_CONFIG` containing the full
   contents of your `config.yaml`.
2. Add a **repository secret** named `RESUME_BASE64` containing your resume
   file base64-encoded:
   ```bash
   base64 -w0 data/resume.pdf   # copy the output
   ```
3. (Optional) Add `SERPAPI_KEY`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`,
   `GMAIL_REFRESH_TOKEN` secrets as described above.
4. The workflow `.github/workflows/daily-job-hunt.yml` runs on a schedule
   (default 07:30 and 19:30 UTC — edit the cron lines for your timezone)
   and can also be triggered manually from the Actions tab
   ("Run workflow").
5. Each run:
   - fetches new postings and scores them against your resume,
   - checks Gmail for new recruiter replies (if configured),
   - writes `reports/latest.md` and commits it back to the repo,
   - posts/updates a **"Daily Job Hunt Report"** GitHub issue so you get a
     notification every run.

## 5. Applying to LinkedIn / Naukri / Unstop postings

These are intentionally **not** auto-applied (see README for why). Two
ways to act on them:

- Click the search links in the daily report/issue and apply normally.
- Or run the local assist tool, which uses **your own logged-in browser**
  and pre-fills the form but leaves the final Submit click to you:

  ```bash
  pip install playwright
  playwright install chromium
  python -m job_hunter.apply_assist --url "<job posting url>" --profile config.yaml
  ```

  The first time, log into LinkedIn/Naukri/Unstop normally in the browser
  window that opens — it uses a persistent profile (`.browser-profile/`)
  so you stay logged in on future runs.

## 6. Deploy the live web app on Render

The `webapp/` folder is a small FastAPI app with a form: upload your resume,
enter job role/location/companies/company type, and get ranked live matches
back in your browser — no GitHub secrets or cron needed for this mode.

1. Go to https://dashboard.render.com → **New → Web Service**.
2. Connect your GitHub account and pick this repository
   (`skills-introduction-to-github`).
3. Since the app lives in a subfolder, set these manually (Render's
   Blueprint auto-detection expects `render.yaml` at the repo root, and
   this repo has other content there too, so manual setup is more
   reliable):
   - **Root Directory:** `job-hunter`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn webapp.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free is fine to start.
4. (Optional) Add an environment variable `SERPAPI_KEY` if you want Google
   Jobs results included.
5. Click **Create Web Service**. Render builds and gives you a public URL
   like `https://job-hunter-assistant.onrender.com`.
6. Open that URL, upload your resume, fill in the form, and submit — it
   calls live RemoteOK/Greenhouse/Lever/Google Jobs feeds and shows ranked
   results directly in the page. Nothing is stored server-side; each
   search is a one-off request.

Note: Render's free plan spins the service down after inactivity, so the
first request after a while takes ~30-60 seconds to wake up — that's
normal, not a bug.

`render.yaml` in this folder documents the same settings as Infrastructure-
as-Code, in case you prefer the Blueprint flow with a custom blueprint path.

## Notes on scope and limits

- `min_match_score` in `config.yaml` controls how loose/strict matching is.
- The skill list lives in `src/job_hunter/skills_taxonomy.py` — add your own
  domain-specific skills/tools there for better matching.
- The SQLite DB (`job_hunter.db`) is what prevents the same posting from
  being reported as "new" every single run.
