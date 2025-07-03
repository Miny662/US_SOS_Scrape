import json
import logging
from bs4 import BeautifulSoup
from util.helpers import clean_text


class ProcessRequest:
    def __init__(self, base_url):
        self.BASE_URL = base_url
        self.SEARCH_API = f"{self.BASE_URL}/corp/Services/MS/CorpServices.asmx/BusinessIdSearch"
        self.DETAILS_URL = f"{self.BASE_URL}/corp/portal/c/page/corpBusinessIdSearch/~/ViewXSLTFileByName.aspx"
        self.HEADERS = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (compatible; BusinessIDScraper/1.0)"
        }

    def get_filing_id(self, session, business_id):
        """Get filing ID for a business ID."""
        payload = json.dumps({"BusinessId": str(business_id)})
        try:
            response = session.post(self.SEARCH_API, headers=self.HEADERS, data=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            inner_json = json.loads(data.get("d", "{}"))
            table = inner_json.get("Table", [])
            if not table:
                return None
            return table[0].get("FilingId")
        except Exception as e:
            logging.debug(f"Error getting FilingId for ID {business_id}: {e}")
            return None

    def get_business_details_html(self, session, filing_id):
        """Get business details HTML for a filing ID."""
        params = {
            "providerName": "MSBSD_CorporationBusinessDetails",
            "FilingId": filing_id
        }
        try:
            response = session.get(self.DETAILS_URL, headers=self.HEADERS, params=params, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logging.debug(f"Error getting details for FilingId {filing_id}: {e}")
            return None

    def parse_printDiv2(self, html):
        """Parse business details from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        main_div = soup.find("div", id="printDiv2")
        if not main_div:
            return {}

        result = {
            "NameHistory": [],
            "BusinessInformation": {},
            "RegisteredAgent": "",
            "OfficersDirectors": []
        }

        try:
            nh_div = main_div.find(lambda tag: tag.name == "div" and "Name History" in tag.text)
            if nh_div:
                nh_table = nh_div.find_next("table", class_="subTable")
                if nh_table:
                    for row in nh_table.find_all("tr")[1:]:
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            result["NameHistory"].append({
                                "Name": clean_text(cols[0].get_text()),
                                "NameType": clean_text(cols[2].get_text())
                            })
        except Exception:
            pass

        try:
            bi_div = main_div.find(lambda tag: tag.name == "div" and "Business Information" in tag.text)
            if bi_div:
                bi_table = bi_div.find_next("table", class_="subTable")
                if bi_table:
                    for row in bi_table.find_all("tr"):
                        cols = row.find_all("td")
                        if len(cols) == 2:
                            key = clean_text(cols[0].get_text()).rstrip(":")
                            val = clean_text(cols[1].get_text())
                            result["BusinessInformation"][key] = val
        except Exception:
            pass

        try:
            ra_div = main_div.find(lambda tag: tag.name == "div" and "Registered Agent" in tag.text)
            if ra_div:
                ra_table = ra_div.find_next("table", class_="subTable")
                if ra_table:
                    td = ra_table.find("td")
                    if td:
                        result["RegisteredAgent"] = clean_text(td.get_text())
        except Exception:
            pass

        try:
            od_div = main_div.find(lambda tag: tag.name == "div" and "Officers & Directors" in tag.text)
            if od_div:
                od_table = od_div.find_next("table", class_="subTable")
                if od_table:
                    for row in od_table.find_all("tr")[1:]:
                        cols = row.find_all("td")
                        if len(cols) >= 3:
                            result["OfficersDirectors"].append({
                                "Name": clean_text(cols[0].get_text(separator=" ")),
                                "Title": clean_text(cols[2].get_text())
                            })
        except Exception:
            pass

        return result
