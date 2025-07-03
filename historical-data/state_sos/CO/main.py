import requests
import json
import random
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from collections import defaultdict
import os

# === CONFIGURATION ===

START_ID = 20250000000
END_ID = 20250700000

PROGRESS_FILE = "progress.txt"
JSONL_FILE = "business_data.jsonl"

PROXY_HOST = "p.webshare.io"
PROXY_PORT = 80
PROXY_PASS = "tjynmmev6t7a"
PROXY_USER_PREFIX = "omuhmvei-"
TOTAL_PROXIES = 1000
SELECTED_PROXIES = 1000
REQUEST_INTERVAL = 0.5  # seconds between requests per proxy
MAX_WORKERS = 50  # Number of concurrent threads
MAX_RETRIES = 5  # Max retries on 429 or transient errors

BASE_URL = "https://www.sos.state.co.us/biz/"

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
}

# === GLOBALS ===

file_lock = Lock()
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

def extract_key_values_from_row(row):
    data = {}
    children = list(row.find_all(['th', 'td'], recursive=False))
    i = 0
    while i < len(children):
        tag = children[i]
        if tag.name == 'th' and tag.has_attr('class') and (
            'entity_conf_column_header_medium' in tag['class'] or
            'entity_conf_column_header_micro' in tag['class']):
            key = tag.get_text(strip=True)
            if i + 1 < len(children) and children[i + 1].name == 'td':
                value = children[i + 1].get_text(" ", strip=True)
                data[key] = value
                i += 2
            else:
                i += 1
        else:
            i += 1
    return data

def extract_section_data(table):
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        row_data = extract_key_values_from_row(row)
        data.update(row_data)
    return data

def parse_main_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    result = {}
    headers = soup.find_all("td", class_="entity_conf_table_header")

    for header in headers:
        section_name = header.get_text(strip=True).lower()
        section_table = header.find_parent("table")
        if not section_table:
            continue

        if "details" in section_name:
            details_data = extract_section_data(section_table)
            result["Details"] = details_data

        elif "registered agent" in section_name:
            reg_agent_data = extract_section_data(section_table)
            result["Registered Agent"] = reg_agent_data

    return result

def parse_history_documents(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    box_div = soup.find(id="box")
    if not box_div:
        return []

    table = box_div.find("table")
    if not table:
        return []

    rows = table.find_all("tr")
    if len(rows) < 2:
        return []

    header_cells = rows[0].find_all("th")
    if len(header_cells) < 2:
        return []

    keys = [th.get_text(strip=True) for th in header_cells[1:]]
    keys = ["Document" if "Document" in k else k for k in keys]

    data_list = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        values = [td.get_text(strip=True) for td in cells[1:]]
        if len(values) != len(keys):
            continue

        row_dict = dict(zip(keys, values))
        data_list.append(row_dict)

    return data_list

def save_as_jsonl(data, filename):
    with file_lock:
        with open(filename, "a", encoding="utf-8") as f:
            json_line = json.dumps(data, ensure_ascii=False)
            f.write(json_line + "\n")

def save_progress(entity_id):
    with file_lock:
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(entity_id))

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return None

def fetch_data_for_id(entity_id, proxy_username):
    retries = 0
    backoff = 5  # seconds initial backoff
    while retries <= MAX_RETRIES:
        rate_limit_proxy(proxy_username)
        proxies = build_proxy_dict(proxy_username)
        session = requests.Session()
        session.proxies.update(proxies)
        session.headers.update(HEADERS)

        try:
            # Main entity page
            entity_url = BASE_URL + "BusinessEntityDetail.do"
            params_entity = {
                "quitButtonDestination": "BusinessEntityCriteriaExt",
                "fileId": str(entity_id),
                "masterFileId": ""
            }
            resp_entity = session.get(entity_url, params=params_entity, timeout=20)
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
            resp_history = session.get(history_url, params=params_history, timeout=20)
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

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", backoff))
                print(f"[{proxy_username}] HTTP 429 error ID {entity_id}, retrying after {retry_after}s")
                time.sleep(retry_after)
                retries += 1
                backoff = min(backoff * 2, 300)
                continue
            else:
                print(f"[{proxy_username}] HTTP error fetching ID {entity_id}: {e}")
                return None
        except Exception as e:
            print(f"[{proxy_username}] Error fetching ID {entity_id}: {e}")
            return None

    print(f"[{proxy_username}] Max retries exceeded for ID {entity_id}")
    return None

def main():
    last_processed = load_progress()
    start_id = last_processed + 1 if last_processed and last_processed >= START_ID else START_ID

    if start_id > END_ID:
        print("All IDs have already been processed.")
        return

    entity_ids = list(range(start_id, END_ID + 1))
    print(f"Processing IDs from {start_id} to {END_ID}...")

    all_proxy_users = [f"{PROXY_USER_PREFIX}{i}" for i in range(1, TOTAL_PROXIES + 1)]
    selected_proxies = random.sample(all_proxy_users, SELECTED_PROXIES)
    print(f"Selected {SELECTED_PROXIES} proxies.")

    proxy_cycle = (selected_proxies[i % SELECTED_PROXIES] for i in range(len(entity_ids)))
    tasks = [(entity_id, proxy_username) for entity_id, proxy_username in zip(entity_ids, proxy_cycle)]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for entity_id, proxy_username in tasks:
            future = executor.submit(fetch_data_for_id, entity_id, proxy_username)
            futures[future] = entity_id

        for future in as_completed(futures):
            entity_id = futures[future]
            result = future.result()
            if result:
                details = result.get("Details")
                if details and isinstance(details, dict) and len(details) > 0:
                    save_as_jsonl(result, JSONL_FILE)
                    id_number = details.get("ID number")
                    if id_number:
                        save_progress(id_number)
                        print(f"Saved data for ID {id_number}")
                    else:
                        print(f"Warning: 'ID number' missing in Details section for ID {entity_id}, skipping progress save.")
                else:
                    print(f"Skipping record with empty or missing Details section for ID {entity_id}.")

    print("All tasks completed.")

if __name__ == "__main__":
    main()
