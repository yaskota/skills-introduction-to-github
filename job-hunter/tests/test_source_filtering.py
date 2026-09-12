from job_hunter.sources.base import keyword_matches


def test_matches_on_individual_words_not_exact_phrase():
    assert keyword_matches(["full stack developer"], "Hiring a Full-Stack Engineer for our team")


def test_matches_compound_keyword_like_node_js():
    assert keyword_matches(["node.js developer"], "Looking for a Node.js Backend Engineer")


def test_no_match_when_nothing_overlaps():
    assert not keyword_matches(["full stack developer"], "Senior Sales Account Executive")
