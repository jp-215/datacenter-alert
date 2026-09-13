"""Persisted seen-set so each story is only alerted once across runs.

Stories are keyed by normalized title (so the same story from two publishers,
or re-crawled on a later day, is treated as already-seen). Falls back to the
link when a normalized title is empty. State is a plain JSON file that the CI
job commits back to the repo after each run.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from .digest import Item, normalize_title

DEFAULT_STATE_PATH = os.path.join("state", "seen.json")

# Forget entries older than this so the file doesn't grow forever. A story that
# ages out and somehow resurfaces months later is fine to re-alert.
DEFAULT_TTL_DAYS = 30.0


def item_key(item: Item) -> str:
    """Stable dedupe key for cross-run tracking."""
    return normalize_title(item.title) or item.link.strip()


@dataclass
class SeenState:
    # key -> last-seen epoch milliseconds
    seen: dict[str, int] = field(default_factory=dict)
    path: str = DEFAULT_STATE_PATH

    @classmethod
    def load(cls, path: str = DEFAULT_STATE_PATH) -> SeenState:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            seen = {str(k): int(v) for k, v in data.get("seen", {}).items()}
        except (FileNotFoundError, ValueError, TypeError):
            seen = {}
        return cls(seen=seen, path=path)

    def is_new(self, item: Item) -> bool:
        return item_key(item) not in self.seen

    def mark(self, items: list[Item], now_ms: int) -> None:
        for it in items:
            self.seen[item_key(it)] = now_ms

    def prune(self, now_ms: int, ttl_days: float = DEFAULT_TTL_DAYS) -> None:
        cutoff = now_ms - int(ttl_days * 86400 * 1000)
        self.seen = {k: ts for k, ts in self.seen.items() if ts >= cutoff}

    def save(self, now_ms: int | None = None) -> None:
        now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        payload = {"updated_ms": now_ms, "seen": self.seen}
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)


def filter_unseen(items: list[Item], state: SeenState) -> list[Item]:
    """Keep only items whose key isn't already in the seen-set."""
    return [it for it in items if state.is_new(it)]
