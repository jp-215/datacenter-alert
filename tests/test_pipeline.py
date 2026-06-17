from dc_alert.config import Config
from dc_alert.notify import chunk, post_discord
from dc_alert.sources import gather, parse_rss, query_url

SAMPLE_RSS = """<?xml version="1.0"?>
<rss><channel>
  <item>
    <title>New Bay Area data center approved - DCD</title>
    <link>http://example.com/a</link>
    <pubDate>Mon, 16 Jun 2026 12:00:00 GMT</pubDate>
    <source url="http://dcd.com">DCD</source>
  </item>
  <item>
    <title>Santa Clara power crunch - Reuters</title>
    <link>http://example.com/b</link>
    <pubDate>Mon, 16 Jun 2026 09:00:00 GMT</pubDate>
  </item>
</channel></rss>"""


def test_query_url_encodes():
    assert "San%20Jose" in query_url("San Jose data center") or "San+Jose" in query_url(
        "San Jose data center"
    )


def test_parse_rss_extracts_items():
    items = parse_rss(SAMPLE_RSS)
    assert len(items) == 2
    assert items[0].title.startswith("New Bay Area")
    assert items[0].link == "http://example.com/a"
    assert items[0].published_ms > 0


def test_gather_with_injected_fetch():
    items = gather(["q1", "q2"], fetch=lambda url: SAMPLE_RSS)
    assert len(items) == 4  # two queries x two items


def test_gather_survives_bad_feed():
    def boom(url):
        raise RuntimeError("network down")

    assert gather(["q"], fetch=boom) == []


def test_chunking_respects_limit():
    text = "\n".join(f"line {i}" for i in range(500))
    parts = chunk(text, limit=200)
    assert all(len(p) <= 200 for p in parts)
    assert "".join(parts).replace("\n", "") == text.replace("\n", "")


def test_post_discord_uses_injected_sender():
    sent = []
    ok = post_discord(
        "http://hook", "hello", post=lambda url, payload: sent.append(payload) or True
    )
    assert ok and sent == [{"content": "hello"}]


def test_config_from_env_defaults():
    cfg = Config.from_env()
    assert cfg.max_items >= 1
    assert cfg.queries
