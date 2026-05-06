import time
import logging
import requests

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; PowerPolicyWatcher/1.0; "
        "+https://github.com/your-org/power-policy-watcher)"
    )
}
TIMEOUT = 20
SLEEP = 2


def fetch(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return resp.text
    except requests.RequestException as e:
        logger.error("Fetch error %s: %s", url, e)
        return None
    finally:
        time.sleep(SLEEP)
