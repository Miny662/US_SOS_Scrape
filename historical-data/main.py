import argparse

from state_sos.MS.scraper import Scraper as MississippiScraper
# from state_sos.DE.scraper import Scraper as DelawareScraper
from state_sos.NY.scraper import Scraper as NewYorkScraper
from state_sos.OH.scraper import Scraper as OhioScraper
from state_sos.PA.scraper import Scraper as PennsylvaniaScraper


def get_scraper(state_code: str):
    state_map = {
        'ms': MississippiScraper(),
        # 'de': DelawareScraper(),
        'ny': NewYorkScraper(state="new_york"),
        'oh': OhioScraper(),
        'pa': PennsylvaniaScraper()
    }
    return state_map[state_code.lower()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", help="state to load", default="ms")
    args = parser.parse_args()
    print(args)
    scraper = get_scraper(args.state)
    scraper.run()
