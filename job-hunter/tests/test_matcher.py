from job_hunter.matcher import score_posting
from job_hunter.sources.base import JobPosting


def test_score_posting_full_match():
    posting = JobPosting(
        source="test", external_id="1", title="Python Backend Engineer",
        company="Acme", location="Remote", url="http://x",
        description="Looking for someone with python, django and aws experience.",
    )
    score, matched = score_posting(posting, {"python", "django", "aws"})
    assert score == 1.0
    assert matched == ["aws", "django", "python"]


def test_score_posting_no_match():
    posting = JobPosting(
        source="test", external_id="2", title="Sales Manager",
        company="Acme", location="Remote", url="http://x",
        description="B2B sales and client relationships.",
    )
    score, matched = score_posting(posting, {"python", "django"})
    assert score == 0.0
    assert matched == []


def test_score_posting_empty_resume_skills():
    posting = JobPosting(
        source="test", external_id="3", title="Anything",
        company="Acme", location="Remote", url="http://x",
    )
    score, matched = score_posting(posting, set())
    assert score == 0.0
