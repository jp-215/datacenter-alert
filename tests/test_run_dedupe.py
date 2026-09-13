"""Integration test: the alert must not repeat the same story across runs."""

import os

from dc_alert import cli
from dc_alert.config import Config

SAMPLE_RSS = """<?xml version="1.0"?>
<rss><channel>
  <item>
    <title>New Bay Area data center approved - DCD</title>
    <link>http://example.com/a</link>
    <pubDate>Mon, 16 Jun 2026 12:00:00 GMT</pubDate>
    <source url="http://dcd.com">DCD</source>
  </item>
</channel></rss>"""

# 2026-06-16 12:00 GMT + a little, so the story is inside the lookback window.
NOW_MS = 1_781_000_000_000


def _config():
    return Config(queries=["q"], lookback_hours=48, max_items=6, discord_webhook="")


def test_story_alerts_once_then_suppressed(tmp_path, monkeypatch):
    # Feed the same RSS on every gather call (network fully stubbed out).
    from dc_alert.sources import parse_rss
    monkeypatch.setattr(cli, "gather", lambda queries: parse_rss(SAMPLE_RSS))
    state_path = os.path.join(tmp_path, "seen.json")

    first = cli.run(_config(), post=True, now_ms=NOW_MS, state_path=state_path)
    assert "New Bay Area data center approved" in first
    assert os.path.exists(state_path)

    second = cli.run(_config(), post=True, now_ms=NOW_MS + 60_000, state_path=state_path)
    assert "New Bay Area data center approved" not in second
    assert "Nothing notable" in second
