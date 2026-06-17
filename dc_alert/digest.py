"""Pure digest logic: parse, filter, dedupe, rank, and format news items.

No network or third-party deps here, so it's all unit-tested.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from email.utils import parsedate_to_datetime


@dataclass(frozen=True)
class Item:
    title: str
    link: str
    source: str
    published_ms: int  # epoch milliseconds (0 if unknown)


def parse_pubdate(value: str) -> int:
    """Parse an RFC-822 RSS date into epoch milliseconds (0 if unparseable)."""
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return 0
    if dt is None:
        return 0
    return int(dt.timestamp() * 1000)


def normalize_title(title: str) -> str:
    """Lowercase, strip a trailing ' - Source' suffix and punctuation, for dedupe."""
    title = re.sub(r"\s+-\s+[^-]+$", "", title)  # drop Google News "- Publisher" tail
    title = re.sub(r"[^a-z0-9 ]", "", title.lower())
    return re.sub(r"\s+", " ", title).strip()


def filter_recent(items: list[Item], now_ms: int, lookback_hours: float) -> list[Item]:
    """Keep items published within the lookback window. Items with unknown date
    (published_ms == 0) are kept so nothing is silently dropped."""
    cutoff = now_ms - int(lookback_hours * 3600 * 1000)
    return [it for it in items if it.published_ms == 0 or it.published_ms >= cutoff]


def dedupe(items: list[Item]) -> list[Item]:
    """Drop duplicate stories by normalized title, keeping the first seen."""
    seen: set[str] = set()
    out: list[Item] = []
    for it in items:
        key = normalize_title(it.title)
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out


def rank(items: list[Item]) -> list[Item]:
    """Most recent first; unknown-date items sink to the bottom."""
    return sorted(items, key=lambda it: it.published_ms, reverse=True)


def build_digest(items: list[Item], now_ms: int, lookback_hours: float,
                 max_items: int) -> list[Item]:
    """Full pipeline: recency filter -> dedupe -> rank -> top N."""
    return rank(dedupe(filter_recent(items, now_ms, lookback_hours)))[:max_items]


def format_digest(items: list[Item], date_str: str, region_label: str) -> str:
    """Render a concise Discord message. Links wrapped in <> to suppress embeds."""
    header = f"🏢 Data Center Alert — {region_label} — {date_str}"
    if not items:
        return f"{header}\nNothing notable in the lookback window."
    lines = [header]
    for it in items:
        src = f" ({it.source})" if it.source else ""
        lines.append(f"- {it.title}{src}\n  <{it.link}>")
    return "\n".join(lines)


def to_records(items: list[Item]) -> list[dict]:
    """Serialize items to plain dicts (for the web dashboard's data.json)."""
    return [
        {
            "title": it.title,
            "link": it.link,
            "source": it.source,
            "published_ms": it.published_ms,
        }
        for it in items
    ]
