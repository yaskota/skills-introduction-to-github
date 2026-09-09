from dataclasses import dataclass, field


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
