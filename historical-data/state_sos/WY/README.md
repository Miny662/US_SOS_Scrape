# Wyoming Business Entity Scraper

This project scrapes business entity information from the Wyoming Secretary of State's website. It uses rotating proxies and multi-threading to efficiently collect data for a range of business filing IDs.

## Features

- Scrapes general information, history, and parties for each business entity
- Uses proxy rotation for anonymity and reliability
- Multi-threaded for fast data collection
- Outputs results in JSONL format in the `output/` directory

## Folder Structure

- `helpers.py` — Data extraction and utility functions
- `process_request.py` — Network and business logic for scraping and parsing
- `scraper.py` — Main entry point for running the scraper
- `requirements.txt` — Python dependencies
- `output/` — Output registry for scraped results

## Installation

1. Clone this repository or copy the WY folder to your machine.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scraper with:

```bash
python scraper.py
```

- The script will create an `output/` directory (if it doesn't exist) and write results to `output/result.jsonl`.
- Each line in the output file is a JSON object with the scraped data for one business entity.

## Configuration

- You can adjust the range of filing IDs, proxy settings, and thread count by editing the variables at the top of `scraper.py`.

## Output

- Results are saved in `output/result.jsonl`.
- Each line is a JSON object with the following structure:
  - `Filing ID`
  - `General information`
  - `History`
  - `Parties`

## Notes

- Make sure you have a valid proxy list and credentials if scraping at scale.
- Respect the website's terms of service and robots.txt.
