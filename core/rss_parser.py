import logging
from datetime import datetime, timedelta, timezone

import feedparser
from bs4 import BeautifulSoup

from core.fetcher import HEADERS

logger = logging.getLogger(__name__)

MAX_ITEMS = 200
MAX_AGE_DAYS = 30

_RSS_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept-Language": HEADERS["Accept-Language"],
}


def _strip_html(text: str) -> str:
    return BeautifulSoup(text, "html.parser").get_text(strip=True)


def _is_recent(entry: dict) -> bool:
    published = entry.get("published_parsed")
    if published is None:
        return True
    entry_dt = datetime(*published[:6], tzinfo=timezone.utc)
    return entry_dt >= datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)


def parse_rss(url: str, site: dict) -> list[dict]:
    feed = feedparser.parse(url, request_headers=_RSS_HEADERS)
    if feed.bozo and not feed.entries:
        logger.error("RSS parse error %s: %s", site["name"], feed.bozo_exception)
        return []
    if not feed.entries:
        logger.warning("Empty RSS feed from %s (status %s)", site["name"], feed.get("status", "unknown"))
        return []

    items = []
    skipped = 0
    for entry in feed.entries[:MAX_ITEMS]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        excerpt = _strip_html(entry.get("summary", ""))
        if not title or not link:
            continue
        if not _is_recent(entry):
            logger.debug("Skipping old entry (%s): %s", site["name"], title[:60])
            skipped += 1
            continue
        items.append({"title": title, "url": link, "excerpt": excerpt})

    if skipped:
        logger.info("Skipped %d old item(s) from %s (older than %d days)", skipped, site["name"], MAX_AGE_DAYS)
    logger.debug("Parsed %d RSS items from %s", len(items), site["name"])
    return items
