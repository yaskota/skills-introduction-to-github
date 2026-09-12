from job_hunter.resume_parser import extract_skills


def test_extract_skills_finds_known_terms():
    text = "Experienced with Python, Django, AWS and Docker. Also know react.js."
    skills = extract_skills(text)
    assert "python" in skills
    assert "django" in skills
    assert "aws" in skills
    assert "docker" in skills
    assert "react.js" in skills


def test_extract_skills_no_partial_matches():
    text = "I write javascript and java."
    skills = extract_skills(text)
    assert "java" in skills
    assert "javascript" in skills
