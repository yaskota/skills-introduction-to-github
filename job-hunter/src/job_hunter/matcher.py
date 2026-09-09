from __future__ import annotations

import re

from .sources.base import JobPosting


def score_posting(posting: JobPosting, resume_skills: set[str]) -> tuple[float, list[str]]:
    """Return (match_score 0..1, matched_skills) based on skill overlap
    between the resume and the posting's title+description."""
    text = f"{posting.title} {posting.description} {' '.join(posting.tags)}".lower()

    matched = []
    for skill in resume_skills:
        pattern = r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])"
        if re.search(pattern, text):
            matched.append(skill)

    if not resume_skills:
        return 0.0, []

    score = len(matched) / len(resume_skills)
    return round(score, 3), sorted(matched)


def rank_postings(
    postings: list[JobPosting], resume_skills: set[str], min_score: float = 0.05
) -> list[dict]:
    ranked = []
    for posting in postings:
        score, matched = score_posting(posting, resume_skills)
        if score >= min_score:
            ranked.append({"posting": posting, "score": score, "matched_skills": matched})
    ranked.sort(key=lambda r: r["score"], reverse=True)
    return ranked
