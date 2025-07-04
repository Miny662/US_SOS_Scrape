import cloudscraper
import json
from bs4 import BeautifulSoup

# Proxy credentials and address
proxy_user = "omuhmvei-1"
proxy_pass = "tjynmmev6t7a"
proxy_host = "p.webshare.io"
proxy_port = "80"

proxy_url = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
proxies = {
    "http": proxy_url,
    "https": proxy_url,
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
}

BASE_URL = "https://www.sos.state.co.us/biz/"

def extract_key_values_from_row(row):
    data = {}
    children = list(row.find_all(['th', 'td'], recursive=False))
    i = 0
    while i < len(children):
        tag = children[i]
        if tag.name == 'th' and tag.has_attr('class') and (
            'entity_conf_column_header_medium' in tag['class'] or
            'entity_conf_column_header_micro' in tag['class']):
            key = tag.get_text(strip=True)
            if i + 1 < len(children) and children[i + 1].name == 'td':
                value = children[i + 1].get_text(" ", strip=True)
                data[key] = value
                i += 2
            else:
                i += 1
        else:
            i += 1
    return data

def extract_section_data(table):
    data = {}
    rows = table.find_all("tr")
    for row in rows:
        row_data = extract_key_values_from_row(row)
        data.update(row_data)
    return data

def parse_main_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    result = {}
    headers = soup.find_all("td", class_="entity_conf_table_header")

    for header in headers:
        section_name = header.get_text(strip=True).lower()
        section_table = header.find_parent("table")
        if not section_table:
            continue

        if "details" in section_name:
            details_data = extract_section_data(section_table)
            result["Details"] = details_data

        elif "registered agent" in section_name:
            reg_agent_data = extract_section_data(section_table)
            result["Registered Agent"] = reg_agent_data

    return result

def parse_history_documents(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    box_div = soup.find(id="box")
    if not box_div:
        print("No element with id='box' found.")
        return []

    table = box_div.find("table")
    if not table:
        print("No table found inside element with id='box'.")
        return []

    rows = table.find_all("tr")
    if not rows or len(rows) < 2:
        print("Table does not have enough rows (need header + data rows).")
        return []

    header_cells = rows[0].find_all("th")
    if len(header_cells) < 2:
        print("Not enough header cells to extract keys.")
        return []

    keys = [th.get_text(strip=True) for th in header_cells[1:]]

    # Post-process keys to change "Document #(click to view)" to "Document"
    keys = ["Document" if "Document" in k else k for k in keys]

    data_list = []
    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue

        values = [td.get_text(strip=True) for td in cells[1:]]

        if len(values) != len(keys):
            continue

        row_dict = dict(zip(keys, values))
        data_list.append(row_dict)

    return data_list

def save_as_jsonl(data, jsonl_filename):
    with open(jsonl_filename, "a", encoding="utf-8") as f:
        json_line = json.dumps(data, ensure_ascii=False)
        f.write(json_line + "\n")

def fetch_entity_and_history(file_id):
    scraper = cloudscraper.create_scraper()  # Use cloudscraper instead of requests.Session()
    scraper.proxies.update(proxies)
    scraper.headers.update(headers)

    # Fetch main entity page
    entity_url = BASE_URL + "BusinessEntityDetail.do"
    params_entity = {
        "quitButtonDestination": "BusinessEntityCriteriaExt",
        "fileId": file_id,
        "masterFileId": ""
    }
    print(f"Fetching entity page for ID {file_id}...")
    response_entity = scraper.get(entity_url, params=params_entity, timeout=15)
    response_entity.raise_for_status()
    data = parse_main_html(response_entity.text)

    # Fetch history and documents page
    history_url = BASE_URL + "BusinessEntityHistory.do"
    params_history = {
        "quitButtonDestination": "BusinessEntityDetail",
        "pi1": "1",
        "nameTyp": "ENT",
        "masterFileId": file_id,
        "entityId2": "",
        "srchTyp": ""
    }
    print(f"Fetching history and documents for ID {file_id}...")
    response_history = scraper.get(history_url, params=params_history, timeout=15)
    response_history.raise_for_status()

    history_data = parse_history_documents(response_history.text)
    data["History and Documents"] = history_data

    return data

def main():
    file_id = "20191823416"  # Replace with your business ID
    data = fetch_entity_and_history(file_id)

    jsonl_file = "business_data.jsonl"
    save_as_jsonl(data, jsonl_file)
    print(f"Extracted data saved to {jsonl_file}")

if __name__ == "__main__":
    main()
