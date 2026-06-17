from dc_alert.digest import (
    Item,
    build_digest,
    dedupe,
    filter_recent,
    format_digest,
    normalize_title,
    parse_pubdate,
    rank,
)

HOUR = 3600 * 1000


def _item(title, ms, link="http://x", source="Src"):
    return Item(title=title, link=link, source=source, published_ms=ms)


def test_parse_pubdate_rfc822():
    assert parse_pubdate("Mon, 16 Jun 2026 12:00:00 GMT") > 0
    assert parse_pubdate("garbage") == 0


def test_normalize_strips_publisher_tail():
    assert normalize_title("Big Data Center Opens - DCD") == "big data center opens"
    assert normalize_title("Big Data Center Opens!") == "big data center opens"


def test_filter_recent_keeps_window_and_unknown():
    now = 1000 * HOUR
    items = [_item("a", now - 10 * HOUR), _item("b", now - 500 * HOUR), _item("c", 0)]
    kept = filter_recent(items, now, lookback_hours=48)
    titles = {it.title for it in kept}
    assert titles == {"a", "c"}  # 'b' too old; 'c' unknown date kept


def test_dedupe_by_normalized_title():
    items = [_item("Data Center Opens - DCD", 1), _item("Data Center Opens - Reuters", 2)]
    assert len(dedupe(items)) == 1


def test_rank_recent_first():
    items = [_item("a", 1 * HOUR), _item("b", 5 * HOUR)]
    assert [it.title for it in rank(items)] == ["b", "a"]


def test_build_digest_pipeline():
    now = 100 * HOUR
    items = [
        _item("Story One - DCD", now - 1 * HOUR),
        _item("Story One - Reuters", now - 2 * HOUR),  # dup
        _item("Story Two", now - 3 * HOUR),
        _item("Ancient", now - 500 * HOUR),            # filtered out
    ]
    out = build_digest(items, now, lookback_hours=48, max_items=5)
    assert [it.title for it in out] == ["Story One - DCD", "Story Two"]


def test_format_digest_empty_and_links():
    assert "Nothing notable" in format_digest([], "2026-06-16", "SF Bay Area")
    text = format_digest([_item("Hi", 1, link="http://e.com")], "2026-06-16", "SF Bay Area")
    assert "<http://e.com>" in text
