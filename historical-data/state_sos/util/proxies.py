from typing import List, Dict

import requests
from state_sos.util.config import CONFIG

GATEWAY_URL = "https://gateway.getpalm.com/v1/proxies"
DEFAULT_HEADERS = {
    "Authorization": f"Bearer {CONFIG.proxy_gateway_api_key}"
}


def get_proxies(service: str = "webshare") -> List[Dict]:
    response = requests.get(url=GATEWAY_URL, headers=DEFAULT_HEADERS, params={"service": service})
    response.raise_for_status()
    return response.json().get('data')