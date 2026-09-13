"""Entry point: gather -> digest -> deliver."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone

from .config import Config
from .digest import build_digest, format_digest, to_records
from .notify import deliver
from .sources import gather
from .state import DEFAULT_STATE_PATH, SeenState, filter_unseen


def run(config: Config, post: bool, now_ms: int | None = None,
        json_path: str | None = None, state_path: str = DEFAULT_STATE_PATH) -> str:
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    raw = gather(config.queries)
    items = build_digest(raw, now_ms, config.lookback_hours, config.max_items)

    # Cross-run dedupe: only alert stories we haven't posted before. Without
    # this, every story inside the lookback window re-posts on each daily run.
    state = SeenState.load(state_path)
    fresh = filter_unseen(items, state)

    date_str = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    text = format_digest(fresh, date_str, config.region_label)
    deliver(text, config.discord_webhook if post else "")

    if post:
        # Record what we just alerted so it never repeats, and keep the file lean.
        state.mark(fresh, now_ms)
        state.prune(now_ms)
        state.save(now_ms)
    if json_path:
        payload = {
            "region": config.region_label,
            "date": date_str,
            "generated_ms": now_ms,
            "items": to_records(items),
        }
        # Dashboard reflects the current window (unfiltered by seen-state).
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print(f"Wrote {json_path}")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SF Bay Area data center news alert")
    parser.add_argument("--post", action="store_true", help="post to the Discord webhook")
    parser.add_argument("--hours", type=float, help="lookback window in hours")
    parser.add_argument("--limit", type=int, help="max items in the digest")
    parser.add_argument("--json", dest="json_path", help="also write the digest to this JSON file")
    parser.add_argument("--state", dest="state_path", default=DEFAULT_STATE_PATH,
                        help="path to the persisted seen-set (default: state/seen.json)")
    args = parser.parse_args(argv)

    config = Config.from_env()
    if args.hours is not None:
        config.lookback_hours = args.hours
    if args.limit is not None:
        config.max_items = args.limit

    run(config, post=args.post, json_path=args.json_path, state_path=args.state_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
