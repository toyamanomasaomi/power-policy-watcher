import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

HISTORY_PATH = Path("data/history.json")


def load_history() -> dict:
    if HISTORY_PATH.exists():
        with HISTORY_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(history: dict) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    logger.info("History saved to %s", HISTORY_PATH)


def find_new_items(site_name: str, items: list[dict], history: dict) -> list[dict]:
    seen_urls: set[str] = set(history.get(site_name, []))
    new_items = [item for item in items if item["url"] not in seen_urls]

    for item in new_items:
        seen_urls.add(item["url"])

    history[site_name] = list(seen_urls)
    return new_items
