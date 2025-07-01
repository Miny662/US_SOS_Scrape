import argparse

from state_sos.MS.scraper import Scraper as MississippiScraper
# from state_sos.DE.scraper import Scraper as DelawareScraper
from state_sos.NY.scraper import Scraper as NewYorkScraper
from state_sos.OH.scraper import Scraper as OhioScraper
from state_sos.PA.scraper import Scraper as PennsylvaniaScraper


def get_scraper(state_code: str, start_id: int = 119999, end_id: int = 120000):
    state_map = {
        'ms': MississippiScraper,
        # 'de': DelawareScraper,
        'ny': NewYorkScraper,
        'oh': OhioScraper,
        'pa': PennsylvaniaScraper
    }
    return state_map[state_code.lower()](start_id=start_id, end_id=end_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", help="state to load", default="ms")
    parser.add_argument("--start_id", help="beginning id", default=119999, type=int)
    parser.add_argument("--end_id", help="ending id", default=120000, type=int)
    args = parser.parse_args()
    print(args)
    scraper = get_scraper(state_code=args.state, start_id=args.start_id, end_id=args.end_id)
    scraper.run()
