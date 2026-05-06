import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_site(html: str, site: dict) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[dict] = []

    for element in soup.select(site["list_selector"]):
        title_el = element.select_one(site.get("title_selector", "a"))
        link_sel = site.get("link_selector")
        link_el = element.select_one(link_sel) if link_sel else None
        # list_selector が <a> 自体を指している場合はその要素をリンクとして使う
        if link_el is None and element.name == "a":
            link_el = element
        excerpt_sel = site.get("excerpt_selector")
        excerpt_el = element.select_one(excerpt_sel) if excerpt_sel else None

        if title_el is None or link_el is None:
            continue

        href = link_el.get("href", "")
        url = urljoin(site.get("base_url", site["url"]), href)
        title = title_el.get_text(strip=True)
        excerpt = excerpt_el.get_text(strip=True) if excerpt_el else ""

        if not title or not url:
            continue

        items.append({"title": title, "url": url, "excerpt": excerpt})

    logger.debug("Parsed %d items from %s", len(items), site["name"])
    return items
