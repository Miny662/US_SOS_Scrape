# Missouri Secretary of State Business Scraper

This project scrapes business entity data from the Missouri Secretary of State website using rotating proxies and concurrent workers. The codebase is modular and inspired by the structure of other state registry scrapers in this repository.

## Project Structure

- `helpers.js` — Utility functions for HTML parsing and delays
- `process_request.js` — Handles proxy/session management, rate limiting, and request/retry logic
- `scraper.js` — Main entry point, orchestrates scraping, workers, and progress
- `package.json` — Node.js dependencies
- `output/` — All output files (JSONL and progress) are stored here

## Setup

1. **Install dependencies:**

   ```bash
   npm install puppeteer-real-browser cheerio
   ```

2. **Run the scraper:**

   ```bash
   npm start
   # or
   node scraper.js
   ```

   The script will:

   - Scrape IDs from 100001 to 200000 (skipping those already completed)
   - Use 15 workers, each waiting 30 seconds between requests
   - Save results to `output/MO_buesiness_data.jsonl`
   - Track completed IDs in `output/progress.txt`

## Output Registry

- All results are saved in the `output/` directory:

  - `output/MO_buesiness_data.jsonl` — Scraped business records in JSON Lines format
  - `output/progress.txt` — List of completed IDs (one per line)

  Example output record:

  ```json
  {
    "ID": 123456,
    "General Information": { ... },
    "Filings": [ ... ],
    "Principal Office Addresses": [ ... ],
    "Contacts": [ ... ]
  }
  ```

## Features

- Rotating proxies for each worker
- Multi-worker scraping for high throughput
- Robust error handling and retry logic
- Modular codebase for easy maintenance
- Resume support: skips IDs already in `progress.txt`

## Customization

- Adjust `startID`, `endID`, `NUM_WORKERS`, and `REQUEST_INTERVAL_MS` in `scraper.js` as needed.
The ID increases to a unique number starting from 22.
- Proxy credentials and logic are in `process_request.js`.

---

**Note:** This tool is for educational and research purposes. Respect the target website's terms of service and robots.txt.
