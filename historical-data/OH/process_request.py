#!/usr/bin/env python
# coding: utf8

import sys
import time
import random
import requests
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
import urllib3

class ProcessRequest(object):
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.clear()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": "https://businesssearch.ohiosos.gov/",
            "Origin": "https://businesssearch.ohiosos.gov",
        }
        self.base_url = "https://businesssearch.ohiosos.gov"
        self.max_retries = 5  # Maximum number of retries for rate limits
        self.initial_backoff = 10  # Initial backoff time in seconds
        self.max_backoff = 300  # Maximum backoff time in seconds (5 minutes)

    # msg script abruptly terminated        
    def script_terminated(self, msg):
        print("___________________________________________________________________________________")
        print("Number of failed attempts. Script abruptly terminated...due to the following error:")
        print("___________________________________________________________________________________")
        print(msg)
        sys.exit()

    # retry 
    def retry(self, n):
        N_ATTEMPS = 150
        WAIT_TIME = 3
        print("reconnecting...", flush=True)
        time.sleep(WAIT_TIME)
        return False if n == N_ATTEMPS else True

    # set request
    def set_request(self, url, params=None, headers=None, verify=None):
        count = 0
        loop = True
        while loop:
            try:
                if params is None:
                    response = self.session.get(url, timeout=60, headers=headers)
                else:
                    response = self.session.post(url, json=params, timeout=60, headers=headers)
                response.raise_for_status()
                loop = (response.status_code != 200)
            except requests.exceptions.HTTPError as httpErr: 
                msg = "Http Error: ", httpErr
                self.session.cookies.clear()
                if response.status_code == 404:
                    return False
            except requests.exceptions.ConnectionError as connErr: 
                msg = "Error Connecting: ", connErr
            except requests.exceptions.Timeout as timeOutErr: 
                msg = "Timeout Error: ", timeOutErr
                return None
            except requests.exceptions.RequestException as reqErr: 
                msg = "Something Else: ", reqErr 
            if loop:
                print(msg)
                count = count + 1
                if not self.retry(count):
                    self.script_terminated(msg)

        return response 

    def handle_rate_limit(self, attempt, entity_number):
        """Handle rate limit with exponential backoff"""
        # Calculate backoff time with exponential increase and some random jitter
        backoff = min(self.initial_backoff * (2 ** attempt) + random.uniform(0, 5), self.max_backoff)
        print(f"Rate limit hit on entity {entity_number}, attempt {attempt + 1}/{self.max_retries}")
        print(f"Waiting {backoff:.1f} seconds before retrying...")
        time.sleep(backoff)

    def call_api(self, entity_number, cookies, max_retries=3):
        """
        Call the API with retry mechanism for both rate limits and other errors.
        Rate limit errors (429) get special handling with more retries and exponential backoff.
        """
        rate_limit_attempts = 0
        general_attempts = 0

        while True:
            try:
                cache_buster = int(time.time() * 1000)
                url = f"https://businesssearchapi.ohiosos.gov/VD_2?entityNumber={entity_number}&_={cache_buster}"
                response = requests.get(url, headers=self.headers, cookies=cookies, timeout=15)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Handle rate limit
                    if rate_limit_attempts < self.max_retries:
                        self.handle_rate_limit(rate_limit_attempts, entity_number)
                        rate_limit_attempts += 1
                        continue
                    else:
                        print(f"Failed to recover from rate limit after {self.max_retries} attempts for entity {entity_number}")
                        return None
                else:
                    print(f"HTTP {response.status_code} on entity {entity_number}")
                    # For other errors, use the general retry mechanism
                    if general_attempts < max_retries:
                        general_attempts += 1
                        time.sleep(2 ** general_attempts)  # Exponential backoff for general errors
                        continue
                    return None

            except requests.RequestException as e:
                print(f"Request error on entity {entity_number}: {e}")
                if general_attempts < max_retries:
                    general_attempts += 1
                    time.sleep(2 ** general_attempts)
                    continue
                return None

    def extract_data(self, data, entity_number):
        try:
            firstpanel = data.get('data', [None]*5)[4]
            listing = data.get('data', [None]*5)[2]

            if firstpanel and isinstance(firstpanel, dict):
                firstpanel_list = firstpanel.get('firstpanel', [])
                if firstpanel_list:
                    info = firstpanel_list[0]
                    business_name = info.get('business_name', 'N/A')
                    entity = info.get('charter_num', 'N/A')
                    filing_type = info.get('business_type', 'N/A')
                    original_filing_date = info.get('effect_date', 'N/A')
                    status = info.get('status', 'N/A')
                    expiry_date = info.get('expiry_date', 'N/A')
                else:
                    return None
            else:
                return None

            filings = []
            if listing and isinstance(listing, dict):
                listing_list = listing.get('listing', [])
                for filing in listing_list:
                    filings.append({
                        "filing_type": filing.get('tran_code_desc', 'N/A'),
                        "date_of_filing": filing.get('effect_date', 'N/A'),
                        "document_id": filing.get('processing_id', 'N/A')
                    })

            # Add source URL to the data
            source_url = f"{self.base_url}/?=businessDetails/{entity_number}"

            return {
                "business_name": business_name,
                "entity": entity,
                "filing_type": filing_type,
                "original_filing_date": original_filing_date,
                "status": status,
                "expiry_date": expiry_date,
                "filings": filings,
                "source_url": source_url
            }
        except Exception as e:
            print(f"Error extracting data: {e}")
            return None 