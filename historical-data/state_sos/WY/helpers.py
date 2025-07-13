import re
from bs4 import BeautifulSoup

def extract_general_info(soup):
    result = {}
    labels = soup.find_all(class_="fieldLabel")
    for label in labels:
        value = label.find_next(class_="fieldData")
        key = label.get_text(strip=True).replace(":", "")
        if value:
            val = value.get_text(separator=" ", strip=True).replace('\n', ' ')
            val = ' '.join(val.split())
            result[key] = val
        else:
            result[key] = ""
    return result

def extract_history(soup):
    history = []
    for container in soup.find_all(class_='fhContainer'):
        record = {}
        title_tag = container.find(class_='fhRef')
        record['Title'] = title_tag.get_text(strip=True) if title_tag else ""
        date_tag = container.find('div', class_='fhDate')
        date_str = ""
        if date_tag:
            match = re.search(r'Date:\s*([0-9/]+)', date_tag.get_text())
            if match:
                date_str = match.group(1)
        record['Date'] = date_str
        details_tag = container.find(class_='fhHistory')
        details = {}
        if details_tag:
            spans = details_tag.find_all('span', class_='resultField')
            i = 0
            while i < len(spans):
                span = spans[i]
                text = span.get_text(separator=" ", strip=True)
                key_match = re.match(r'(.+?)\s*#?\s*Changed\s*From:', text)
                if key_match:
                    key = key_match.group(1).strip()
                    from_value = ""
                    next_node = span.next_sibling
                    while next_node and (not isinstance(next_node, str) or not next_node.strip()):
                        next_node = next_node.next_sibling
                    if next_node:
                        from_value = str(next_node).strip()
                    to_value = ""
                    if i + 1 < len(spans):
                        to_span = spans[i+1]
                        to_text = to_span.get_text(separator=" ", strip=True)
                        if to_text.startswith("To:"):
                            to_next = to_span.next_sibling
                            while to_next and (not isinstance(to_next, str) or not to_next.strip()):
                                to_next = to_next.next_sibling
                            if to_next:
                                to_value = str(to_next).strip()
                            i += 1
                    details[key] = {"From": from_value, "To": to_value}
                i += 1
        if details:
            record['Details'] = details
        history.append(record)
    return history

def extract_parties(soup):
    parties = []
    div = soup.find('div', id='divParties')
    if not div:
        return parties
    for li in div.select('li.rowRegular'):
        party = {}
        role_tag = li.find(class_='resHist1')
        party['Role'] = role_tag.get_text(strip=True).replace('(', '').replace(')', '') if role_tag else ""
        org_tag = li.find(class_='resHist2')
        if org_tag:
            org_field = org_tag.find(class_='resultField')
            org_name = org_field.next_sibling if org_field and org_field.next_sibling else ""
            org_name = str(org_name).replace('\n', ' ')
            org_name = ' '.join(org_name.split())
            party['Organization'] = org_name
        else:
            party['Organization'] = ""
        addr_tag = li.find(class_='resHist3')
        if addr_tag:
            addr_field = addr_tag.find(class_='resultField')
            addr = addr_field.next_sibling if addr_field and addr_field.next_sibling else ""
            addr = str(addr).replace('\n', ' ')
            addr = ' '.join(addr.split())
            party['Address'] = addr
        else:
            party['Address'] = ""
        parties.append(party)
    return parties

def is_nonempty_data(general_info, history, parties):
    return bool(general_info) or bool(history) or bool(parties) 