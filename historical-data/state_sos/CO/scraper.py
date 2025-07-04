import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from process_request import fetch_data_for_id
from helpers import save_as_jsonl, save_progress, load_progress

# === CONFIGURATION ===
START_ID = 20250000000
END_ID = 20250700000
OUTPUT_DIR = "output"
PROGRESS_FILE = os.path.join(OUTPUT_DIR, "progress.txt")
JSONL_FILE = os.path.join(OUTPUT_DIR, "CO_business_data.jsonl")
TOTAL_PROXIES = 1000
SELECTED_PROXIES = 1000
MAX_WORKERS = 50


def main():
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    last_processed = load_progress(PROGRESS_FILE)
    start_id = last_processed + 1 if last_processed and last_processed >= START_ID else START_ID
    if start_id > END_ID:
        print("All IDs have already been processed.")
        return
    entity_ids = list(range(start_id, END_ID + 1))
    print(f"Processing IDs from {start_id} to {END_ID}...")
    all_proxy_users = [f"omuhmvei-{i}" for i in range(1, TOTAL_PROXIES + 1)]
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
                        save_progress(id_number, PROGRESS_FILE)
                        print(f"Saved data for ID {id_number}")
                    else:
                        print(f"Warning: 'ID number' missing in Details section for ID {entity_id}, skipping progress save.")
                else:
                    print(f"Skipping record with empty or missing Details section for ID {entity_id}.")
    print("All tasks completed.")

if __name__ == "__main__":
    main() 