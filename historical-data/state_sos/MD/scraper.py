import json
import os
from bs4 import BeautifulSoup
from helpers import Helpers
from process_request import ProcessRequest

class Scraper:
    def __init__(self, business_id, output_jsonl_file):
        self.business_id = business_id
        self.output_jsonl_file = output_jsonl_file
        self.helpers = Helpers()
        self.pr = ProcessRequest()
        # Ensure output directory exists
        output_dir = os.path.dirname(self.output_jsonl_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def run(self):
        try:
            print("\n--- Step 1: Load initial search page ---")
            initial_token, initial_html = self.pr.get_verification_token_and_html(self.pr.PAGE_URL)
            print(f"Initial __RequestVerificationToken: {initial_token}")

            print("\n--- Step 2: Solve first CAPTCHA ---")
            captcha_id_1 = self.pr.submit_captcha_to_2captcha(self.pr.SITE_KEY, self.pr.PAGE_URL)
            captcha_token_1 = self.pr.poll_captcha_solution(captcha_id_1)
            print(f"First CAPTCHA token: {captcha_token_1[:30]}...")

            print("\n--- Step 3: Submit search form ---")
            search_html = self.pr.submit_search_form(initial_token, captcha_token_1, self.business_id)

            print("\n--- Step 4: Extract token from search result HTML ---")
            personal_property_token = self.pr.extract_token_from_search_html(search_html)
            print(f"Extracted Personal Property token from search HTML: {personal_property_token}")

            # Parse search result data
            soup_search = BeautifulSoup(search_html, 'html.parser')
            general_info = self.helpers.extract_general_info(soup_search)
            filing_history = self.helpers.extract_filing_history(soup_search)

            print("\n--- Step 5: Solve second CAPTCHA ---")
            captcha_id_2 = self.pr.submit_captcha_to_2captcha(self.pr.SITE_KEY, self.pr.PERSONAL_PROPERTY_URL_TEMPLATE.format(self.business_id))
            captcha_token_2 = self.pr.poll_captcha_solution(captcha_id_2)
            print(f"Second CAPTCHA token: {captcha_token_2[:30]}...")

            print("\n--- Step 6: Submit Personal Property form ---")
            personal_property_html = self.pr.submit_personal_property_form(personal_property_token, captcha_token_2, self.business_id)

            # Parse personal property data
            soup_personal = BeautifulSoup(personal_property_html, 'html.parser')
            annual_report = self.helpers.extract_table_by_index(soup_personal, 0)
            assessments_summary = self.helpers.extract_table_by_index(soup_personal, 1)

            combined_result = {
                'Business ID': self.business_id,
                'General Information': general_info,
                'Filing History': filing_history,
                'Annual Report/Personal Property Tax Filings': annual_report,
                'Personal Property Assessments Summary': assessments_summary,
            }

            # Write to JSONL file
            with open(self.output_jsonl_file, 'a', encoding='utf-8') as f_out:
                json_line = json.dumps(combined_result, ensure_ascii=False)
                f_out.write(json_line + '\n')

            print(f"\nData extraction complete. Results saved to {self.output_jsonl_file}")

        except Exception as e:
            print(f"\nError: {e}")

if __name__ == '__main__':
    BUSINESS_ID = 'F04608014'  # Replace with your target business ID
    OUTPUT_JSONL_FILE = os.path.join('output', 'MD_businesses_result.jsonl')
    Scraper(BUSINESS_ID, OUTPUT_JSONL_FILE).run() 