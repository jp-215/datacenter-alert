"""Configuration for the data center alert, from defaults + environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

# Search queries — Bay Area / Northern California data center coverage.
DEFAULT_QUERIES = [
    "Bay Area data center",
    "San Francisco data center",
    "Silicon Valley data center",
    "San Jose data center",
    "Santa Clara data center",
]


@dataclass
class Config:
    queries: list[str] = field(default_factory=lambda: list(DEFAULT_QUERIES))
    region_label: str = "SF Bay Area"
    lookback_hours: float = 48.0
    max_items: int = 6
    discord_webhook: str = ""

    @classmethod
    def from_env(cls) -> Config:
        queries = os.getenv("DC_ALERT_QUERIES", "")
        return cls(
            queries=[q.strip() for q in queries.split(";") if q.strip()] or list(DEFAULT_QUERIES),
            region_label=os.getenv("DC_ALERT_REGION", cls.region_label),
            lookback_hours=float(os.getenv("DC_ALERT_LOOKBACK_HOURS", cls.lookback_hours)),
            max_items=int(os.getenv("DC_ALERT_MAX_ITEMS", cls.max_items)),
            discord_webhook=os.getenv("DISCORD_WEBHOOK_URL", ""),
        )
