import cloudscraper
import time
from collections import defaultdict
from threading import Lock
from helpers import parse_main_html, parse_history_documents

PROXY_HOST = "p.webshare.io"
PROXY_PORT = 80
PROXY_PASS = "tjynmmev6t7a"
PROXY_USER_PREFIX = "omuhmvei-"
REQUEST_INTERVAL = 0.5
MAX_RETRIES = 5
BASE_URL = "https://www.sos.state.co.us/biz/"
HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
}

proxy_last_request_time = defaultdict(float)
proxy_lock = defaultdict(Lock)

def build_proxy_dict(username):
    proxy_url = f"http://{username}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    return {
        "http": proxy_url,
        "https": proxy_url,
    }

def rate_limit_proxy(username):
    with proxy_lock[username]:
        elapsed = time.time() - proxy_last_request_time[username]
        wait_time = REQUEST_INTERVAL - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
        proxy_last_request_time[username] = time.time()

def fetch_data_for_id(entity_id, proxy_username):
    retries = 0
    backoff = 5  # seconds initial backoff
    while retries <= MAX_RETRIES:
        rate_limit_proxy(proxy_username)
        proxies = build_proxy_dict(proxy_username)
        scraper = cloudscraper.create_scraper()
        scraper.proxies.update(proxies)
        scraper.headers.update(HEADERS)
        try:
            # Main entity page
            entity_url = BASE_URL + "BusinessEntityDetail.do"
            params_entity = {
                "quitButtonDestination": "BusinessEntityCriteriaExt",
                "fileId": str(entity_id),
                "masterFileId": ""
            }
            resp_entity = scraper.get(entity_url, params=params_entity, timeout=20)
            if resp_entity.status_code == 429:
                retry_after = int(resp_entity.headers.get("Retry-After", backoff))
                print(f"[{proxy_username}] 429 on main page ID {entity_id}, retrying after {retry_after}s")
                time.sleep(retry_after)
                retries += 1
                backoff = min(backoff * 2, 300)  # exponential backoff capped at 5 minutes
                continue
            resp_entity.raise_for_status()
            main_data = parse_main_html(resp_entity.text)

            # History and documents page
            history_url = BASE_URL + "BusinessEntityHistory.do"
            params_history = {
                "quitButtonDestination": "BusinessEntityDetail",
                "pi1": "1",
                "nameTyp": "ENT",
                "masterFileId": str(entity_id),
                "entityId2": "",
                "srchTyp": ""
            }
            resp_history = scraper.get(history_url, params=params_history, timeout=20)
            if resp_history.status_code == 429:
                retry_after = int(resp_history.headers.get("Retry-After", backoff))
                print(f"[{proxy_username}] 429 on history page ID {entity_id}, retrying after {retry_after}s")
                time.sleep(retry_after)
                retries += 1
                backoff = min(backoff * 2, 300)
                continue
            resp_history.raise_for_status()
            history_data = parse_history_documents(resp_history.text)

            main_data["History and Documents"] = history_data

            return main_data

        except Exception as e:
            # cloudscraper raises requests.exceptions.HTTPError for 4xx/5xx
            if hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 429:
                retry_after = int(getattr(e.response, 'headers', {}).get("Retry-After", backoff))
                print(f"[{proxy_username}] HTTP 429 error ID {entity_id}, retrying after {retry_after}s")
                time.sleep(retry_after)
                retries += 1
                backoff = min(backoff * 2, 300)
                continue
            print(f"[{proxy_username}] Error fetching ID {entity_id}: {e}")
            return None

    print(f"[{proxy_username}] Max retries exceeded for ID {entity_id}")
    return None 