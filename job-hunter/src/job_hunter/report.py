from __future__ import annotations

from datetime import datetime, timezone


def render_report(counts: dict, new_matches: list[dict], new_replies: list[dict],
                   assist_links: dict | None = None) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Job Hunt Report - {now}",
        "",
        "## Summary",
        f"- New matching jobs found: **{counts['new_matches']}**",
        f"- Applications sent today: **{counts['applied_today']}**",
        f"- Recruiter replies today: **{counts['replies_today']}**",
        f"- Total applications so far: **{counts['total_applied']}**",
        "",
    ]

    if new_replies:
        lines.append("## Replies received")
        for r in new_replies:
            lines.append(f"- **From:** {r['from']} | **Subject:** {r['subject']} ({r['date']})")
        lines.append("")

    if new_matches:
        lines.append("## New matching postings (auto-sourced, ranked by fit)")
        for m in new_matches[:25]:
            p = m["posting"]
            pct = round(m["score"] * 100)
            lines.append(
                f"- **[{p.title}]({p.url})** at {p.company} ({p.location}) "
                f"— {pct}% skill match — via {p.source}"
            )
        lines.append("")

    if assist_links:
        lines.append("## LinkedIn / Naukri / Unstop (manual review required)")
        lines.append(
            "These platforms block automated scraping/applying, so here are "
            "direct search links for today's target keywords — open, review, "
            "and apply yourself (or use `apply_assist.py` locally to "
            "pre-fill the form):"
        )
        for name, url in assist_links.items():
            lines.append(f"- [{name.title()} search]({url})")
        lines.append("")

    if not new_matches and not new_replies:
        lines.append("_No new matches or replies since the last run._")

    return "\n".join(lines)
