## Scraper historical data palm-historical-data-oh:

Historical Information Tracker for Searching for Ohio Secretary of State Businesses (SOS OH)

This project includes a scraper specifically designed to search all historical data on the Ohio Secretary of State (SOS OH) website. Its primary function is to extract all available business information by consecutively iterating over all business IDs.

📋 Prerequisites

Python 3.9+

🛠️ Quick Start

1. Run scraper.py

The input parameters are within the scraper:

START_ID
END_ID

It can be run from a VPS or Google Collab notebook swarm.

## 🏗️ Project Structure

```text
├── scraper.py                # Core parser logic and data extraction
├── process_request.py        # Handles initial HTTP requests (uses `requests` library)
├── helpers.py               # Contains help functions
├── requirements.txt         # Libraries required for execution
└── README.md               # Project documentation
```

## Output:

The scraper returns a JSONL file named after the scraper execution date.
