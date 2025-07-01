#!/usr/bin/env python
# coding: utf8

import time
import random
import requests
import undetected_chromedriver as uc

class ProcessRequest:
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.clear()
        self.driver = None

    def set_proxy(self, url: str, port: str, user: str, password: str) -> None:
        self.session.proxies = {
            "http": f"http://{user}:{password}@{url}:{port}",
            "https": f"http://{user}:{password}@{url}:{port}"
        }

    def get_cookies_and_driver(self, url):
        options = uc.ChromeOptions()
        # Uncomment below if you want headless mode (may affect CAPTCHA solving)
        # options.add_argument("--headless")
        self.driver = uc.Chrome(options=options)
        self.driver.get(url)
        input("Solve CAPTCHA manually, then press Enter to continue...")
        return self.driver

    def get_cookies(self):
        selenium_cookies = self.driver.get_cookies()
        return {c['name']: c['value'] for c in selenium_cookies}

    def get_headers(self):
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": "https://businesssearch.ohiosos.gov/",
            "Origin": "https://businesssearch.ohiosos.gov",
        }

    def call_api_with_browser(self, entity_number, max_retries=8):
        cookies = self.get_cookies()
        headers = self.get_headers()
        
        retry_count = 0
        while retry_count < max_retries:
            try:
                url = f"https://businesssearchapi.ohiosos.gov/VD_{entity_number}?_={int(time.time()*1000)}"
                response = requests.get(url, headers=headers, cookies=cookies, timeout=20)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    print(f"Rate limit hit on entity {entity_number}, waiting 10 minutes...")
                    time.sleep(600)
                    continue
                elif response.status_code == 403:
                    print(f"HTTP 403 Forbidden - CAPTCHA likely expired")
                    self.driver.refresh()
                    input("Solve CAPTCHA manually, then press Enter to continue...")
                    cookies = self.get_cookies()
                    retry_count += 1
                else:
                    delay = min((2 ** retry_count) + random.uniform(0, 2), 60)
                    print(f"HTTP {response.status_code} error. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    retry_count += 1
                    
            except requests.RequestException as e:
                delay = min((2 ** retry_count) + random.uniform(0, 2), 60)
                print(f"Request error: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                retry_count += 1
                
        print(f"Failed after {max_retries} attempts for entity {entity_number}")
        return None

    def cleanup(self):
        if self.driver:
            self.driver.quit() 