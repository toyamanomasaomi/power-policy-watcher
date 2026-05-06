import logging
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

MAX_ITEMS = 200


def _strip_html(text: str) -> str:
    return BeautifulSoup(text, "html.parser").get_text(strip=True)


def parse_rss(url: str, site: dict) -> list[dict]:
    feed = feedparser.parse(url)
    if feed.bozo and not feed.entries:
        logger.error("RSS parse error %s: %s", site["name"], feed.bozo_exception)
        return []

    items = []
    for entry in feed.entries[:MAX_ITEMS]:
        title = entry.get("title", "").strip()
        link = entry.get("link", "").strip()
        excerpt = _strip_html(entry.get("summary", ""))
        if not title or not link:
            continue
        items.append({"title": title, "url": link, "excerpt": excerpt})

    logger.debug("Parsed %d RSS items from %s", len(items), site["name"])
    return items
