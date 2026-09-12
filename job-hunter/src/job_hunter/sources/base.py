from dataclasses import dataclass, field

STOPWORDS = {"the", "and", "for", "with", "developer", "engineer", "of", "in", "a"}


def keyword_matches(keywords: list[str], haystack: str) -> bool:
    """Loose match: a posting counts if it contains any *significant word*
    from any of the search keywords - not the whole phrase verbatim.
    Real postings rarely repeat a search phrase like "full stack developer"
    word-for-word (they say "Full-Stack Engineer", "Node.js Backend Dev",
    etc.), so requiring the exact phrase filtered out almost everything.
    Precision is recovered downstream by resume-skill-based ranking."""
    haystack = haystack.lower()
    for keyword in keywords:
        words = [w for w in keyword.lower().split() if w not in STOPWORDS and len(w) >= 3]
        words = words or [keyword.lower()]
        if any(word in haystack for word in words):
            return True
    return False


@dataclass
class JobPosting:
    source: str
    external_id: str
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    posted_at: str = ""
    tags: list[str] = field(default_factory=list)

    @property
    def dedupe_key(self) -> str:
        return f"{self.source}:{self.external_id}"
