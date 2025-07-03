# Colorado S# Colorado Secretary of State Business Scraper

This project scrapes business entity data from the Colorado Secretary of State website using rotating proxies and concurrent requests. The codebase is modular and follows the structure of the NY registry scrapers.

## Project Structure

- `helpers.py` — Utility functions for HTML parsing and file I/O
- `process_request.py` — Handles proxy/session management, rate limiting, and request/retry logic
- `scraper.py` — Main entry point, orchestrates scraping, threading, and progress
- `requirements.txt` — Python dependencies
- `output/` — All output files (JSONL and progress) are stored here

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper:**
   ```bash
   python scraper.py
   ```

## Output Registry

- All results are saved in the `output/` directory:
  - `output/CO_business_data.jsonl` — Scraped business records in JSON Lines format
  - `output/progress.txt` — Last processed ID for resuming scraping

## Features

- Rotating proxies for each request
- Threaded scraping for high throughput
- Robust error handling and retry logic
- Modular codebase for easy maintenance

## Customization

- Adjust `START_ID`, `END_ID`, and other parameters in `scraper.py` as needed.
- The output directory can be changed by modifying the `OUTPUT_DIR` variable in `scraper.py`.

---

**Note:** This tool is for educational and research purposes. Respect the target website's terms of service and robots.txt.
ecretary of State Business Scraper

This project scrapes business entity data from the Colorado Secretary of State website using rotating proxies and concurrent requests. The codebase is modular and follows the structure of the NY registry scrapers.

## Project Structure

- `helpers.py` — Utility functions for HTML parsing and file I/O
- `process_request.py` — Handles proxy/session management, rate limiting, and request/retry logic
- `scraper.py` — Main entry point, orchestrates scraping, threading, and progress
- `requirements.txt` — Python dependencies
- `output/` — All output files (JSONL and progress) are stored here

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper:**
   ```bash
   python scraper.py
   ```

## Output Registry

- All results are saved in the `output/` directory:
  - `output/CO_business_data.jsonl` — Scraped business records in JSON Lines format
  - `output/progress.txt` — Last processed ID for resuming scraping

## Features

- Rotating proxies for each request
- Threaded scraping for high throughput
- Robust error handling and retry logic
- Modular codebase for easy maintenance

## Customization

- Adjust `START_ID`, `END_ID`, and other parameters in `scraper.py` as needed.
- The output directory can be changed by modifying the `OUTPUT_DIR` variable in `scraper.py`.

---

**Note:** This tool is for educational and research purposes. Respect the target website's terms of service and robots.txt.
