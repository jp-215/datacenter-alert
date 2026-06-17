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


def run(config: Config, post: bool, now_ms: int | None = None,
        json_path: str | None = None) -> str:
    now_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    raw = gather(config.queries)
    items = build_digest(raw, now_ms, config.lookback_hours, config.max_items)
    date_str = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
    text = format_digest(items, date_str, config.region_label)
    deliver(text, config.discord_webhook if post else "")
    if json_path:
        payload = {
            "region": config.region_label,
            "date": date_str,
            "generated_ms": now_ms,
            "items": to_records(items),
        }
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
    args = parser.parse_args(argv)

    config = Config.from_env()
    if args.hours is not None:
        config.lookback_hours = args.hours
    if args.limit is not None:
        config.max_items = args.limit

    run(config, post=args.post, json_path=args.json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
