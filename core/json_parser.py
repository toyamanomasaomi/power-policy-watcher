import logging
from urllib.parse import urljoin

import requests

from core.fetcher import HEADERS, TIMEOUT

logger = logging.getLogger(__name__)

MAX_ITEMS = 20


def parse_json_api(url: str, site: dict) -> list[dict]:
    # brotli はrequestsが自動解凍できないため除外する
    headers = {**HEADERS, "Accept-Encoding": "gzip, deflate", **site.get("extra_headers", {})}
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        if not resp.text.strip():
            logger.error("Empty response from %s (status %d)", site["name"], resp.status_code)
            return []
        data = resp.json()
    except ValueError as e:
        logger.error("JSON parse error %s: %s | body: %.200s", site["name"], e, resp.text)
        return []
    except Exception as e:
        logger.error("JSON fetch error %s: %s", site["name"], e)
        return []

    base_url = site.get("base_url", "")
    title_key = site.get("json_title_key", "title")
    url_key = site.get("json_url_key", "url")
    items = []

    for entry in data[:MAX_ITEMS]:
        title = entry.get(title_key, "").strip()
        link = entry.get(url_key, "").strip()
        if not title or not link:
            continue
        full_url = urljoin(base_url, link) if base_url else link
        items.append({"title": title, "url": full_url, "excerpt": ""})

    logger.debug("Parsed %d JSON items from %s", len(items), site["name"])
    return items
