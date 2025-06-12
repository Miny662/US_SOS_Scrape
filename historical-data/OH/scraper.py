#!/usr/bin/env python
# coding: utf8

import undetected_chromedriver as uc
import time
import signal
from process_request import ProcessRequest
from helpers import Helpers

def safe_quit(self):
    try:
        original_quit(self)
    except OSError as e:
        if getattr(e, 'winerror', None) == 6:
            pass
        else:
            raise

# Store the original quit method
original_quit = uc.Chrome.quit
# Replace with our safe version
uc.Chrome.quit = safe_quit

class OhioScraper:
    def __init__(self):
        self.base_url = "https://businesssearch.ohiosos.gov"
        self.processor = ProcessRequest()
        self.helpers = Helpers()
        self.save_interval = 100  # Save every 100 records
        self.current_id = None
        self.current_batch = []
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_interrupt)
        signal.signal(signal.SIGTERM, self.handle_interrupt)

    def handle_interrupt(self, signum, frame):
        """Handle interrupt signals by saving current progress"""
        print("\nReceived interrupt signal. Saving progress...")
        if self.current_id is not None and self.current_batch:
            self.helpers.save_checkpoint(self.current_id - 1, self.current_batch)
        raise KeyboardInterrupt

    def get_cookies(self, url):
        options = uc.ChromeOptions()
        driver = uc.Chrome(options=options)
        try:
            driver.get(url)
            input("Solve CAPTCHA manually, then press Enter to continue...")
            selenium_cookies = driver.get_cookies()
            cookies = {c['name']: c['value'] for c in selenium_cookies}
            return cookies
        finally:
            time.sleep(0.5)
            driver.quit()

    def process_records(self, start_id, end_id, cookies):
        """Process a range of business records"""
        self.current_batch = []
        
        try:
            for entity_id in range(start_id, end_id + 1):
                self.current_id = entity_id
                print(f"Fetching data for entity ID {entity_id}...")
                data = self.processor.call_api(str(entity_id), cookies)
                extracted = self.processor.extract_data(data, entity_id) if data else None

                if extracted:
                    print(f"  Got data: {extracted['business_name']}")
                    print(f"  URL: {extracted['source_url']}")
                else:
                    print(f"  No valid data for entity ID {entity_id}")

                self.current_batch.append(extracted)

                # Save progress every save_interval records
                if len(self.current_batch) >= self.save_interval:
                    self.helpers.save_checkpoint(entity_id, self.current_batch)
                    self.current_batch = []  # Clear the batch after saving

                time.sleep(3)  # Delay to avoid rate limits

            # Save any remaining records in the final batch
            if self.current_batch:
                self.helpers.save_checkpoint(end_id, self.current_batch)

        except Exception as e:
            # In case of error, save the current batch and re-raise the exception
            if self.current_batch:
                last_id = self.current_id - 1 if self.current_id else start_id
                self.helpers.save_checkpoint(last_id, self.current_batch)
            raise

    def run(self, start_id=None, end_id=1200000):
        """Run the scraper"""
        # Load last processed ID from checkpoint if no start_id provided
        if start_id is None:
            start_id = self.helpers.load_checkpoint() + 1

        if start_id > end_id:
            print("Start ID is greater than end ID. Nothing to process.")
            return

        print(f"Starting scrape from ID {start_id} to {end_id}")
        start_url = "https://businesssearch.ohiosos.gov/?=businessDetails/1"
        
        try:
            cookies = self.get_cookies(start_url)
            self.process_records(start_id, end_id, cookies)
            print("\nScraping completed successfully!")

        except KeyboardInterrupt:
            print("\nScraping interrupted by user. Progress has been saved.")
        except Exception as e:
            print(f"\nAn error occurred: {e}")
        finally:
            # One final save attempt in case of any unsaved data
            if self.current_batch and self.current_id:
                try:
                    self.helpers.save_checkpoint(self.current_id - 1, self.current_batch)
                except Exception as e:
                    print(f"Error saving final checkpoint: {e}")
            print("\nScraping session ended. You can resume from the last checkpoint later.")

if __name__ == "__main__":
    scraper = OhioScraper()
    scraper.run() 




    