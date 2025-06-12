import undetected_chromedriver as uc
import requests
import time
import json
import pandas as pd

original_quit = uc.Chrome.quit
def safe_quit(self):
    try:
        original_quit(self)
    except OSError as e:
        if getattr(e, 'winerror', None) == 6:
            pass
        else:
            raise
uc.Chrome.quit = safe_quit

def get_cookies(url):
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

def call_api(entity_number, cookies, max_retries=3):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": "https://businesssearch.ohiosos.gov/",
        "Origin": "https://businesssearch.ohiosos.gov",
    }
    for attempt in range(max_retries):
        try:
            cache_buster = int(time.time() * 1000)
            url = f"https://businesssearchapi.ohiosos.gov/VD_2?entityNumber={entity_number}&_={cache_buster}"
            response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                print(f"Rate limit hit on entity {entity_number}, retrying after delay...")
            else:
                print(f"HTTP {response.status_code} on entity {entity_number}")
        except requests.RequestException as e:
            print(f"Request error on entity {entity_number}: {e}")

        # Exponential backoff before retrying
        time.sleep(2 ** attempt)
    print(f"Failed to fetch data for entity {entity_number} after {max_retries} attempts.")
    return None

def extract_data(data):
    # Same extraction logic as before (omitted here for brevity)
    # Return None if no valid data found
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

        return {
            "business_name": business_name,
            "entity": entity,
            "filing_type": filing_type,
            "original_filing_date": original_filing_date,
            "status": status,
            "expiry_date": expiry_date,
            "filings": filings
        }
    except Exception as e:
        print(f"Error extracting data: {e}")
        return None

def save_partial_data(data_list, json_path, csv_path):
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=2)

    records_main = []
    records_filings = []

    for entry in data_list:
        if not entry:
            continue
        main = {
            "business_name": entry.get("business_name", "N/A"),
            "entity": entry.get("entity", "N/A"),
            "filing_type": entry.get("filing_type", "N/A"),
            "original_filing_date": entry.get("original_filing_date", "N/A"),
            "status": entry.get("status", "N/A"),
            "expiry_date": entry.get("expiry_date", "N/A"),
        }
        records_main.append(main)

        for filing in entry.get("filings", []):
            filing_record = filing.copy()
            filing_record["entity"] = main["entity"]
            records_filings.append(filing_record)

    df_main = pd.DataFrame(records_main)
    df_filings = pd.DataFrame(records_filings)

    df_main.to_csv(csv_path.replace('.csv', '_main.csv'), index=False)
    df_filings.to_csv(csv_path.replace('.csv', '_filings.csv'), index=False)

    print(f"Saved partial data to {json_path} and CSV files.")

def main():
    start_url = "https://businesssearch.ohiosos.gov/?=businessDetails/1"
    cookies = get_cookies(start_url)

    all_data = []
    save_interval = 10  # Save every 10 requests

    for entity_id in range(1, 101):
        print(f"Fetching data for entity ID {entity_id}...")
        data = call_api(str(entity_id), cookies)
        extracted = extract_data(data) if data else None

        if extracted:
            print(f"  Got data: {extracted['business_name']}")
        else:
            print(f"  No valid data for entity ID {entity_id}")

        all_data.append(extracted)

        if entity_id % save_interval == 0:
            save_partial_data(all_data, "ohio_business_data_partial.json", "ohio_business_data_partial.csv")

        time.sleep(3) 

    save_partial_data(all_data, "ohio_business_data_all.json", "ohio_business_data_all.csv")

if __name__ == "__main__":
    main()
