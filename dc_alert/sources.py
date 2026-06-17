"""Fetch news items from Google News RSS (no API key required).

Parsing uses only the standard library. The HTTP fetch is injectable so the
pipeline can be tested offline with canned RSS.
"""

from __future__ import annotations

import urllib.parse
import urllib.request
from xml.etree import ElementTree

from .digest import Item, parse_pubdate

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
USER_AGENT = "datacenter-alert/0.1 (+https://github.com)"


def query_url(query: str) -> str:
    return GOOGLE_NEWS_RSS.format(q=urllib.parse.quote(query))


def parse_rss(xml_text: str) -> list[Item]:
    """Parse an RSS document into Items."""
    root = ElementTree.fromstring(xml_text)
    items: list[Item] = []
    for node in root.iterfind(".//item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        pub = node.findtext("pubDate") or ""
        source = (node.findtext("source") or "").strip()
        if title and link:
            items.append(Item(title=title, link=link, source=source,
                              published_ms=parse_pubdate(pub)))
    return items


def _http_get(url: str, timeout: float = 15.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted host)
        return resp.read().decode("utf-8", errors="replace")


def gather(queries: list[str], fetch=_http_get) -> list[Item]:
    """Fetch and merge items across all queries. ``fetch`` is injectable for tests."""
    items: list[Item] = []
    for query in queries:
        try:
            items.extend(parse_rss(fetch(query_url(query))))
        except Exception as exc:  # one bad feed shouldn't kill the run
            print(f"WARN: query failed ({query!r}): {exc}")
    return items
