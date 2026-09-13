import os

from dc_alert.digest import Item
from dc_alert.state import SeenState, filter_unseen, item_key

HOUR = 3600 * 1000
DAY = 24 * HOUR


def _item(title, link="http://x", source="Src", ms=0):
    return Item(title=title, link=link, source=source, published_ms=ms)


def test_item_key_normalizes_and_dedups_publishers():
    a = _item("Data Center Opens - DCD")
    b = _item("Data Center Opens - Reuters")
    assert item_key(a) == item_key(b) == "data center opens"


def test_item_key_falls_back_to_link_when_title_blank():
    it = _item("!!!", link="http://example.com/story")
    assert item_key(it) == "http://example.com/story"


def test_filter_unseen_drops_known(tmp_path):
    path = os.path.join(tmp_path, "seen.json")
    state = SeenState(path=path)
    old = _item("Old Story")
    state.mark([old], now_ms=1000)

    items = [old, _item("Brand New Story")]
    fresh = filter_unseen(items, state)
    assert [it.title for it in fresh] == ["Brand New Story"]


def test_roundtrip_persists_seen(tmp_path):
    path = os.path.join(tmp_path, "seen.json")
    s1 = SeenState(path=path)
    s1.mark([_item("A"), _item("B")], now_ms=5000)
    s1.save(now_ms=5000)

    s2 = SeenState.load(path)
    assert not s2.is_new(_item("A"))
    assert s2.is_new(_item("C"))


def test_prune_forgets_old_entries(tmp_path):
    path = os.path.join(tmp_path, "seen.json")
    state = SeenState(path=path)
    now = 100 * DAY
    state.mark([_item("Recent")], now_ms=now)
    state.seen["stale key"] = now - 40 * DAY  # older than 30d TTL
    state.prune(now, ttl_days=30)
    assert "stale key" not in state.seen
    assert not state.is_new(_item("Recent"))


def test_load_missing_file_is_empty(tmp_path):
    state = SeenState.load(os.path.join(tmp_path, "nope.json"))
    assert state.seen == {}
