import re
from bs4 import BeautifulSoup

class Helpers:
    def __init__(self):
        pass

    def clean_text(self, text):
        text = text.replace('\u0000', '')
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_general_info(self, soup):
        data = {}
        form_items = soup.find_all(class_='fp_formItem')
        for item in form_items:
            key_tag = item.find(class_='fp_formItemLabel')
            if not key_tag:
                continue
            key = self.clean_text(key_tag.get_text(strip=True).rstrip(':'))
            value_container = item.find(class_='fp_formItemData')
            if not value_container:
                continue
            raw_html = value_container.decode_contents()
            parts = [BeautifulSoup(part, 'html.parser').get_text() for part in raw_html.split('<br/>')]
            lines = [self.clean_text(part) for part in parts if self.clean_text(part)]
            if len(lines) == 1:
                data[key] = lines[0]
            else:
                data[key] = lines
        return data

    def extract_filing_history(self, soup):
        table = soup.find('table', id='tblFilingHistory')
        if not table:
            return []
        thead = table.find('thead')
        headers = [th.get_text(strip=True) for th in thead.find_all('th')] if thead else []
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else []
        data_list = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) != len(headers):
                continue
            row_data = {headers[i]: cells[i].get_text(strip=True) for i in range(len(headers))}
            data_list.append(row_data)
        return data_list

    def extract_table_by_index(self, soup, table_index=0):
        tables = soup.find_all('table')
        if len(tables) <= table_index:
            return []
        table = tables[table_index]
        thead = table.find('thead')
        keys = [th.get_text(strip=True) for th in thead.find_all('th')] if thead else []
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else []
        data_list = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) != len(keys):
                continue
            row_data = {keys[i]: cells[i].get_text(strip=True) for i in range(len(keys))}
            data_list.append(row_data)
        return data_list 