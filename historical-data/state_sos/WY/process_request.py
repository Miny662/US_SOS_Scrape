import requests
import random
import time
import os
from bs4 import BeautifulSoup
from helpers import extract_general_info, extract_history, extract_parties, is_nonempty_data

base_url = "https://wyobiz.wyo.gov/Business/"

def get_detail_link_from_search(filing_id, proxy_url, max_retries=3):
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            headers_get = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": base_url + "FilingSearch.aspx"
            }
            resp = session.get(base_url+"FilingSearch.aspx", headers=headers_get, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            viewstate = soup.find(id="__VIEWSTATE")['value']
            viewstategenerator = soup.find(id="__VIEWSTATEGENERATOR")['value']
            eventvalidation = soup.find(id="__EVENTVALIDATION")['value']
            post_data = {
                '__VIEWSTATE': viewstate,
                '__VIEWSTATEGENERATOR': viewstategenerator,
                '__EVENTVALIDATION': eventvalidation,
                '__ASYNCPOST': 'true',
                'ctl00$MainContent$myScriptManager': 'ctl00$MainContent$UpdatePanel1|ctl00$MainContent$cmdSearch',
                'ctl00$MainContent$txtFilingID': filing_id,
                'ctl00$MainContent$txtFilingName': '',
                'ctl00$MainContent$searchOpt': '0',
                'chkSearchStartWith': 'on',          
                'ctl00$MainContent$cmdSearch': ' Search',
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
            }
            headers_post = {
                "User-Agent": headers_get["User-Agent"],
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-Requested-With": "XMLHttpRequest",
                "X-MicrosoftAjax": "Delta=true",
                "Origin": "https://wyobiz.wyo.gov",
                "Referer": base_url+"FilingSearch.aspx",
            }
            post_resp = session.post(base_url+"FilingSearch.aspx", data=post_data, headers=headers_post, timeout=20)
            post_resp.raise_for_status()
            ajax_blocks = post_resp.text.split('|')
            detail_html = None
            for block in ajax_blocks:
                if 'rowRegular' in block:
                    detail_html = block
                    break
            if not detail_html:
                return None, None
            soup = BeautifulSoup(detail_html, 'html.parser')
            li = soup.find('li', class_="rowRegular")
            a_tag = li.find('a', href=True) if li else None
            if not a_tag:
                return None, detail_html  # No detail link, but return HTML for debug if needed
            detail_link = a_tag['href']
            if not detail_link.startswith("http"):
                detail_link = base_url + detail_link.lstrip('/')
            return detail_link, None
        except Exception as e:
            print(f"Search error for {filing_id} on attempt {attempt+1}: {e}")
            time.sleep(random.uniform(0.5, 2.0))
    return None, None

def get_business_detail_html(detail_link, proxy_url, max_retries=5):
    html = None
    for attempt in range(max_retries):
        try:
            session = requests.Session()
            session.proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            headers_get = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": base_url + "FilingSearch.aspx"
            }
            detail_resp = session.get(detail_link, headers=headers_get, timeout=20)
            detail_resp.raise_for_status()
            html = detail_resp.text
            return html
        except Exception as e:
            print(f"Detail error for {detail_link} on attempt {attempt+1}: {e}")
            time.sleep(random.uniform(0.5, 2.0))
    return html

def get_and_parse_detail(filing_num, detail_link, proxy_url, max_retries=5):
    html = None
    for attempt in range(max_retries):
        html = get_business_detail_html(detail_link, proxy_url)
        if html is None:
            print(f"Attempt {attempt+1}: Failed to fetch detail page for {filing_num}. Retrying...")
            continue
        soup = BeautifulSoup(html, "html.parser")
        general_info = extract_general_info(soup)
        history = extract_history(soup)
        parties = extract_parties(soup)
        if is_nonempty_data(general_info, history, parties):
            return {
                "Filing ID": filing_num,
                "General information": general_info,
                "History": history,
                "Parties": parties
            }
        else:
            print(f"Attempt {attempt+1}: Empty detail data for {filing_num}. Retrying...")
        time.sleep(random.uniform(0.5, 2.0))
    # Save the last HTML for debugging
    debug_dir = "debug_html"
    os.makedirs(debug_dir, exist_ok=True)
    with open(os.path.join(debug_dir, f"{filing_num}_detail.html"), "w", encoding="utf-8") as f:
        f.write(html if html else "")
    print(f"Failed to get non-empty detail data for {filing_num} after {max_retries} attempts.")
    return {
        "Filing ID": filing_num,
        "General information": {},
        "History": [],
        "Parties": []
    }

def process_id(filing_num, proxy_url):
    detail_link, debug_html = get_detail_link_from_search(filing_num, proxy_url)
    if not detail_link:
        print(f"No detail link for {filing_num}, skipping.")
        if debug_html:
            debug_dir = "debug_html"
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, f"{filing_num}_search.html"), "w", encoding="utf-8") as f:
                f.write(debug_html)
        return None
    result = get_and_parse_detail(filing_num, detail_link, proxy_url, max_retries=5)
    print(f"Saved: {filing_num}")
    return result 