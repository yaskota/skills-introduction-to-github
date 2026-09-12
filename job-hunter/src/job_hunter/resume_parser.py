"""Extract raw text and a skill set from a resume file (.pdf, .docx, .txt)."""
from __future__ import annotations

import re
from pathlib import Path

from .skills_taxonomy import SKILLS_TAXONOMY


def extract_text(resume_path: str) -> str:
    path = Path(resume_path)
    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {resume_path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import pdfplumber

        text_parts = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)

    if suffix == ".docx":
        import docx

        doc = docx.Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"Unsupported resume format: {suffix}")


def extract_skills(text: str, taxonomy: list[str] | None = None) -> set[str]:
    """Match known skills against resume text using word-boundary search
    (case-insensitive). Simple and dependency-free, good enough for ranking
    postings by overlap."""
    taxonomy = taxonomy or SKILLS_TAXONOMY
    lowered = text.lower()
    found = set()
    for skill in taxonomy:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            found.add(skill.lower())
    return found


def parse_resume(resume_path: str) -> dict:
    text = extract_text(resume_path)
    skills = extract_skills(text)
    return {"path": resume_path, "text": text, "skills": sorted(skills)}


if __name__ == "__main__":
    import sys

    result = parse_resume(sys.argv[1])
    print(f"Found {len(result['skills'])} skills:")
    for s in result["skills"]:
        print(f"  - {s}")
