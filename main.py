import os
import sys
import logging
import yaml

from core.fetcher import fetch
from core.parser import parse_site
from core.rss_parser import parse_rss
from core.diff import load_history, save_history, find_new_items
from core.mailer import send_mail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

SUMMARIZER_MODE = os.environ.get("SUMMARIZER_MODE", "none").lower()

if SUMMARIZER_MODE == "sumy":
    from core.summarizer_sumy import summarize
else:
    from core.summarizer_none import summarize


def load_sites(path: str = "config/sites.yaml") -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["sites"]


def main() -> None:
    sites = load_sites()
    history = load_history()
    all_new_items: list[dict] = []

    for site in sites:
        logger.info("Fetching: %s", site["name"])
        if site.get("type") == "rss":
            items = parse_rss(site["url"], site)
        else:
            html = fetch(site["url"])
            if html is None:
                logger.warning("Skip %s (fetch failed)", site["name"])
                continue
            items = parse_site(html, site)
        new_items = find_new_items(site["name"], items, history)
        logger.info("%s: %d new item(s)", site["name"], len(new_items))

        for item in new_items:
            item["summary"] = summarize(item.get("excerpt", ""))
            item["site_name"] = site["name"]
            all_new_items.append(item)

    save_history(history)
    if all_new_items:
        send_mail(all_new_items)
        logger.info("Mail sent. %d new item(s) total.", len(all_new_items))
    else:
        logger.info("No new items found.")


if __name__ == "__main__":
    main()
