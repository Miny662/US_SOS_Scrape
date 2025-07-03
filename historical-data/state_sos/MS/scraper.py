import os
import json
import time
import logging
import threading
import requests

from util.proxy_manager import randomize_proxy
from util.request_helper import get_proxies
from state_sos.MS.process_request import ProcessRequest
from util.helpers import get_data_files, load_range_progress, save_range_progress
from state_sos.base_scraper import BaseScraper

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')


class Scraper(BaseScraper):
    def __init__(self, start_id: int = 1, end_id: int = 7800000):
        super().__init__(start_id, end_id)
        self.BASE_URL = "https://corp.sos.ms.gov"
        # self.PROXY_FILE = "./state_sos/MS/Webshare 1000 proxies - option 1.txt"
        self.OUTPUT_DIR = "Output"
        self.MERGED_FILE = os.path.join(self.OUTPUT_DIR, "merged_data.jsonl")
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

        self.START_ID = 650001
        self.TOTAL_IDS = 500
        self.END_ID = self.START_ID + self.TOTAL_IDS - 1
        self.REQUEST_INTERVAL = 1.0

        self.process_request = ProcessRequest(self.BASE_URL)

    def load_proxies(self, filename):
        """Load proxies from file."""
        proxies = []
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(":")
                if len(parts) != 4:
                    logging.warning(f"Skipping invalid proxy line: {line}")
                    continue
                host, port, user, password = parts
                proxy_url = f"http://{user}:{password}@{host}:{port}"
                proxies.append(proxy_url)
        return proxies

    def worker(self, proxy_url, start_id, end_id):
        """Worker function for each proxy thread."""
        session = requests.Session()
        session.proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        output_file = os.path.join(self.OUTPUT_DIR, f"data_ids_{start_id}_to_{end_id}.jsonl")
        progress_file = os.path.join(self.OUTPUT_DIR, f"progress_ids_{start_id}_to_{end_id}.json")

        last_completed_id = load_range_progress(progress_file, start_id)
        logging.info(f"Proxy for IDs {start_id}-{end_id} resuming from {last_completed_id + 1}")

        count = 0
        for business_id in range(last_completed_id + 1, end_id + 1):
            start_time = time.time()
            filing_id = self.process_request.get_filing_id(session, business_id)
            if filing_id:
                html = self.process_request.get_business_details_html(session, filing_id)
                if html:
                    data = self.process_request.parse_printDiv2(html)
                    data["BusinessId"] = business_id
                    data["FilingId"] = filing_id
                    with open(output_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(data, ensure_ascii=False) + "\n")
                    count += 1
                    logging.info(
                        f"Proxy for IDs {start_id}-{end_id}: Saved Business ID {business_id} (Total saved: {count})")
                else:
                    logging.warning(f"Proxy for IDs {start_id}-{end_id}: No HTML for Business ID {business_id}")
            else:
                logging.info(f"Proxy for IDs {start_id}-{end_id}: No data for Business ID {business_id}")

            save_range_progress(progress_file, business_id)

            elapsed = time.time() - start_time
            if elapsed < self.REQUEST_INTERVAL:
                time.sleep(self.REQUEST_INTERVAL - elapsed)

        logging.info(f"Proxy for IDs {start_id}-{end_id} finished. Total saved: {count}")

        try:
            if os.path.exists(progress_file):
                os.remove(progress_file)
                logging.info(f"Deleted progress file {progress_file} after completion.")
        except Exception as e:
            logging.error(f"Failed to delete progress file {progress_file}: {e}")

    def merge_files(self, files, output_file):
        """Merge all data files into a single sorted file."""
        all_records = []
        for file in files:
            logging.info(f"Reading {file}")
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        all_records.append(record)
                    except json.JSONDecodeError as e:
                        logging.warning(f"Skipping invalid JSON line in {file}: {e}")

            try:
                os.remove(file)
                logging.info(f"Deleted merged file: {file}")
            except Exception as e:
                logging.error(f"Failed to delete file {file}: {e}")

        logging.info(f"Sorting {len(all_records)} records by BusinessId")
        all_records.sort(key=lambda x: x.get("BusinessId", 0))

        logging.info(f"Writing merged data to {output_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            for record in all_records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        logging.info("Merge completed.")

    def run(self):
        """Run the scraper."""
        # @deprecated
        # proxies = self.load_proxies(self.PROXY_FILE)
        proxies = get_proxies(service="webshare")
        if len(proxies) < 100:
            logging.error("Not enough proxies loaded. Need at least 100.")
            return

        # selected_proxies = random.sample(proxies, 100)
        selected_proxies = randomize_proxy(proxies, limit=100, single_endpoint=True, shuffle=True)
        logging.info(f"Selected 100 proxies for scraping.")

        ids_per_proxy = self.TOTAL_IDS // 100
        remainder = self.TOTAL_IDS % 100

        threads = []
        current_start = self.START_ID

        for i, proxy_url in enumerate(selected_proxies):
            extra = 1 if i < remainder else 0
            current_end = current_start + ids_per_proxy + extra - 1

            t = threading.Thread(target=self.worker, args=(proxy_url, current_start, current_end), daemon=True)
            threads.append(t)
            t.start()

            logging.info(f"Assigned IDs {current_start} to {current_end} to proxy {i + 1}")

            current_start = current_end + 1

        for t in threads:
            t.join()

        logging.info("All scraping threads have finished.")

        logging.info("Starting data merging process...")
        data_files_to_merge = get_data_files(self.OUTPUT_DIR)
        if not data_files_to_merge:
            logging.error("No data files found to merge after scraping.")
        else:
            self.merge_files(data_files_to_merge, self.MERGED_FILE)
            logging.info(f"All data merged into {self.MERGED_FILE}")


if __name__ == "__main__":
    Scraper().run()
