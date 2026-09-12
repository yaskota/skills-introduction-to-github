"""Live web app: upload a resume, enter job specs, get ranked matches
from real job sources right away. Runs standalone (no cron, no DB) -
each request is a one-off search. Deployable on Render (see render.yaml)."""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from job_hunter.resume_parser import extract_skills, extract_text  # noqa: E402
from job_hunter.matcher import rank_postings  # noqa: E402
from job_hunter.sources import remoteok, greenhouse, lever, google_jobs  # noqa: E402
from job_hunter.sources.assist_links import build_search_links  # noqa: E402

app = FastAPI(title="Job Hunter Assistant")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/api/health")
def health():
    return {"status": "ok"}


def _split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


@app.post("/api/search")
async def search(
    resume: UploadFile = File(...),
    job_role: str = Form(...),
    location: str = Form(""),
    count: int = Form(20),
    companies: str = Form(""),
    company_type: str = Form(""),
    min_score: float = Form(0.05),
):
    suffix = Path(resume.filename or "resume.txt").suffix or ".txt"
    if suffix.lower() not in (".pdf", ".docx", ".txt", ".md"):
        raise HTTPException(400, "Resume must be .pdf, .docx, or .txt")

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await resume.read())
        tmp_path = tmp.name

    try:
        text = extract_text(tmp_path)
    finally:
        os.unlink(tmp_path)

    resume_skills = extract_skills(text)

    keywords = _split_csv(job_role)
    if company_type:
        keywords = keywords + _split_csv(company_type)
    target_companies = _split_csv(companies)

    postings = []
    source_errors = []

    def _safe_fetch(label: str, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - one flaky source shouldn't fail the request
            source_errors.append(f"{label}: {exc}")
            return []

    postings += _safe_fetch("remoteok", remoteok.fetch, query_keywords=keywords, limit=100)
    if target_companies:
        postings += _safe_fetch("greenhouse", greenhouse.fetch, target_companies, query_keywords=keywords)
        postings += _safe_fetch("lever", lever.fetch, target_companies, query_keywords=keywords)
    for kw in keywords[:3]:  # cap external calls per request
        postings += _safe_fetch("google_jobs", google_jobs.fetch, kw, location=location, limit=20)

    if target_companies:
        wanted = [c.lower() for c in target_companies]
        postings = [
            p for p in postings
            if any(w in p.company.lower() for w in wanted) or p.source in ("greenhouse", "lever")
        ]

    ranked = rank_postings(postings, resume_skills, min_score=min_score)[:count]

    results = [
        {
            "title": r["posting"].title,
            "company": r["posting"].company,
            "location": r["posting"].location,
            "url": r["posting"].url,
            "source": r["posting"].source,
            "score_pct": round(r["score"] * 100),
            "matched_skills": r["matched_skills"],
        }
        for r in ranked
    ]

    return {
        "resume_skills": sorted(resume_skills),
        "results_count": len(results),
        "results": results,
        "assist_links": build_search_links(keywords[0] if keywords else "", location),
        "source_errors": source_errors,
        "note": (
            "LinkedIn/Naukri/Unstop aren't scraped automatically (against "
            "their Terms of Service) - use the search links above, or the "
            "local apply_assist.py tool, to apply there."
        ),
    }
