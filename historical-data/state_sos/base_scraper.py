import datetime
from typing import Dict, List

from state_sos.util.aws import write_file_to_s3
from state_sos.util.config import CONFIG
from state_sos.util.proxies import get_proxies


class BaseScraper:
    STATE: str
    state_code: str
    s3_source_key_prefix: str = "sources/sos"
    proxies: List[Dict]

    def __init__(self, start_id: int = 1, end_id: int = 7800000):
        self.START_ID = start_id
        self.END_ID = end_id
        self.proxies = get_proxies()

    def write_to_s3(self, item: Dict, item_id: str):
        write_file_to_s3(
            bucket=CONFIG.pdp_source_bucket,
            key=f"{self.s3_source_key_prefix}/{self.state_code}/{datetime.date.today()}/{item_id}.json",
            data=item,
        )

