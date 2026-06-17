"""Entry point: gather -> digest -> deliver."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timezone

from .config import Config
from .digest import build_digest, format_digest
from .notify import deliver
from .sources import gather


def run(config: Config, post: bool, now_ms: int | None = None) -> str:
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    raw = gather(config.queries)
    items = build_digest(raw, now_ms, config.lookback_hours, config.max_items)
    date_str = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    text = format_digest(items, date_str, config.region_label)
    deliver(text, config.discord_webhook if post else "")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SF Bay Area data center news alert")
    parser.add_argument("--post", action="store_true", help="post to the Discord webhook")
    parser.add_argument("--hours", type=float, help="lookback window in hours")
    parser.add_argument("--limit", type=int, help="max items in the digest")
    args = parser.parse_args(argv)

    config = Config.from_env()
    if args.hours is not None:
        config.lookback_hours = args.hours
    if args.limit is not None:
        config.max_items = args.limit

    run(config, post=args.post)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
