import time
import requests
from bs4 import BeautifulSoup

class ProcessRequest:
    def __init__(self):
        self.API_KEY = 'ee4cd9fa0e6e99116fbcb8ccdaf2aa02'  # Your 2Captcha API key
        self.SITE_KEY = '6Lc01PUUAAAAAMyGmpXYkDCdKdbPdnOFXpXbP4O8'  # reCAPTCHA site key (same for both CAPTCHAs)
        self.PAGE_URL = 'https://egov.maryland.gov/BusinessExpress/EntitySearch'
        self.SEARCH_POST_URL = 'https://egov.maryland.gov/BusinessExpress/EntitySearch/Business'
        self.PERSONAL_PROPERTY_URL_TEMPLATE = 'https://egov.maryland.gov/BusinessExpress/EntitySearch/PersonalPropertyReturns/{}'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def get_verification_token_and_html(self, url):
        resp = self.session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        token_input = soup.find('input', {'name': '__RequestVerificationToken'})
        if not token_input:
            raise Exception(f'__RequestVerificationToken not found on {url}')
        return token_input['value'], resp.text

    def submit_captcha_to_2captcha(self, site_key, page_url):
        params = {
            'key': self.API_KEY,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': self.PAGE_URL,
            'json': 1,
        }
        print(f"Submitting CAPTCHA to 2Captcha for {page_url}...")
        resp = requests.get('http://2captcha.com/in.php', params=params)
        data = resp.json()
        if data['status'] != 1:
            raise Exception(f"2Captcha submit error: {data['request']}")
        print(f"Captcha submitted, ID: {data['request']}")
        return data['request']

    def poll_captcha_solution(self, captcha_id, timeout=180, interval=5):
        url = 'http://2captcha.com/res.php'
        print(f"Polling 2Captcha for solution to CAPTCHA ID: {captcha_id}...")
        for _ in range(0, timeout, interval):
            time.sleep(interval)
            params = {'key': self.API_KEY, 'action': 'get', 'id': captcha_id, 'json': 1}
            resp = requests.get(url, params=params)
            data = resp.json()
            if data['status'] == 1:
                print("Captcha solved!")
                return data['request']
            elif data['request'] == 'CAPCHA_NOT_READY':
                print("Waiting for captcha solution...")
            else:
                raise Exception(f"2Captcha polling error: {data['request']}")
        raise Exception("Captcha solving timed out.")

    def submit_search_form(self, verification_token, g_recaptcha_response, business_id):
        data = {
            '__RequestVerificationToken': verification_token,
            'g-recaptcha-response': g_recaptcha_response,
            'BusinessDepartmentId': business_id,
            'TabToShow': '0',
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': self.PAGE_URL,
            'Origin': 'https://egov.maryland.gov',
        }
        resp = self.session.post(self.SEARCH_POST_URL, data=data, headers=headers)
        resp.raise_for_status()
        return resp.text

    def extract_token_from_search_html(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        token_input = soup.find('input', {'name': '__RequestVerificationToken'})
        if not token_input:
            raise Exception('__RequestVerificationToken not found in search HTML')
        return token_input['value']

    def submit_personal_property_form(self, verification_token, g_recaptcha_response, business_id):
        data = {
            '__RequestVerificationToken': verification_token,
            'g-recaptcha-response': g_recaptcha_response,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Referer': self.SEARCH_POST_URL,
            'Origin': 'https://egov.maryland.gov',
            'X-Requested-With': 'XMLHttpRequest',
        }
        url = self.PERSONAL_PROPERTY_URL_TEMPLATE.format(business_id)
        resp = self.session.post(url, data=data, headers=headers)
        resp.raise_for_status()
        return resp.text 