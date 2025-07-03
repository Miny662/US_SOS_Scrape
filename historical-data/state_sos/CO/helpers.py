import json
import os
from bs4 import BeautifulSoup
from threading import Lock

file_lock = Lock()


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
        return []
    table = box_div.find("table")
    if not table:
        return []
    rows = table.find_all("tr")
    if len(rows) < 2:
        return []
    header_cells = rows[0].find_all("th")
    if len(header_cells) < 2:
        return []
    keys = [th.get_text(strip=True) for th in header_cells[1:]]
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

def save_as_jsonl(data, filename):
    with file_lock:
        with open(filename, "a", encoding="utf-8") as f:
            json_line = json.dumps(data, ensure_ascii=False)
            f.write(json_line + "\n")

def save_progress(entity_id, progress_file):
    with file_lock:
        with open(progress_file, "w") as f:
            f.write(str(entity_id))

def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return None 