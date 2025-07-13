import os
import random
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from process_request import process_id

start_year = 2021
start_num = 1057894
end_num = 1069994
proxy_host = "p.webshare.io"
proxy_port = 80
proxy_pass = "tjynmmev6t7a"
all_usernames = [f"omuhmvei-{i}" for i in range(1, 1001)]
selected_usernames = random.sample(all_usernames, 100)
proxy_list = [
    f"http://{username}:{proxy_pass}@{proxy_host}:{proxy_port}"
    for username in selected_usernames
]

def generate_filing_ids(start_year, start_num, end_num):
    for num in range(start_num, end_num + 1):
        yield f"{start_year}-{num:09d}"

def main():
    filing_ids = list(generate_filing_ids(start_year, start_num, end_num))
    random.shuffle(filing_ids)
    jobs = [(filing_id, proxy_list[i % len(proxy_list)]) for i, filing_id in enumerate(filing_ids)]
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "result.jsonl")
    with ThreadPoolExecutor(max_workers=100) as executor, open(output_file, "a", encoding="utf-8") as f:
        futures = [executor.submit(process_id, filing_id, proxy_url) for filing_id, proxy_url in jobs]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                f.write(json.dumps(result, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main() 