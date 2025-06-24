#!/usr/bin/env python
# coding: utf8

import time
import random
from .process_request import ProcessRequest
from .helpers import Helpers
from state_sos.base_scraper import BaseScraper


class Scraper(BaseScraper):
    def __init__(self, start_id: int = 1, end_id: int = 120000):
        super().__init__(start_id, end_id)
        self.pr = ProcessRequest()
        self.helpers = Helpers()

        # Use output directory for file paths
        self.DATA_FILE = self.helpers.get_output_path("ohio_business_data.jsonl")
        self.CHECKPOINT_FILE = self.helpers.get_output_path("checkpoint.txt")
        self.STATE = 'ohio'
        self.state_code = 'oh'

    def extract_data(self, data, entity_id):
        try:
            data_list = data.get('data', [])
            if len(data_list) < 5:
                print("Unexpected data format or missing panels")
                return None

            firstpanel = data_list[4]
            listing = data_list[2]

            info = firstpanel.get('firstpanel', [{}])[0]
            filings = [{
                "filing_type": f.get('tran_code_desc'),
                "date_of_filing": f.get('effect_date'),
                "document_id": f.get('processing_id')
            } for f in listing.get('listing', [])]

            if not info.get('business_name'):
                print("No business name found, skipping")
                return None

            return {
                "business_name": info.get('business_name'),
                "entity": info.get('charter_num'),
                "filing_type": info.get('business_type'),
                "original_filing_date": info.get('effect_date'),
                "status": info.get('status'),
                "expiry_date": info.get('expiry_date'),
                "filings": filings,
                "url": f"https://businesssearch.ohiosos.gov/?=businessDetails/{entity_id}"
            }
        except Exception as e:
            print(f"Data extraction error: {e}")
            return None

    def jsonl_out(self, items):
        if items:
            self.helpers.save_to_jsonl(items, self.DATA_FILE)

    def parser_items(self, entity_id):
        print(f"Processing entity {entity_id} - URL: https://businesssearch.ohiosos.gov/?=businessDetails/{entity_id}")
        data = self.pr.call_api_with_browser(str(entity_id))

        if data:
            extracted = self.extract_data(data, entity_id)
            if extracted:
                self.write_to_s3(extracted, entity_id)
                return True
            else:
                print(f"No valid data for entity {entity_id}, skipping.")
                return True
        return False

    def run(self):
        self.pr.get_cookies_and_driver("https://businesssearch.ohiosos.gov/")
        entity_id = self.helpers.load_checkpoint(self.CHECKPOINT_FILE)

        try:
            while entity_id < self.END_ID and not self.helpers.STOP_SIGNAL:
                success = self.parser_items(entity_id)

                if success:
                    entity_id += 1
                    self.helpers.save_checkpoint(entity_id, self.CHECKPOINT_FILE)
                else:
                    print(f"Failed to fetch data for entity {entity_id}, retrying same ID after delay...")
                    time.sleep(30)
                    continue

                time.sleep(random.uniform(4, 6))

        finally:
            self.pr.cleanup()
            print("Clean shutdown completed.")


if __name__ == "__main__":
    Scraper().run()
