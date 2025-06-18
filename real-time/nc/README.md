### Scraper Real Time palm-realtime-nc:

Real-Time Scraper for Nort Carolina Secretary of State (SOS Nort Carolina) Business Search

This project features a scraper designed specifically for conducting real-time searches on the Nort Carolina Secretary of State (SOS Nort Carolina) website. Its primary function is to extract business information using the company's identification number (Business ID).

🚀 Automated Selenium Scraper on AWS Lambda (Containerized)
Deploy a Python + requests + Bs4 scraper as a serverless Lambda function using Docker.

📋 Prerequisites

Python 3.9+

🛠️ Quick Start

Automatic deployment process in an AWS Lambda function


## 🏗️ Project Structure

```text
.
├── Dockerfile                # Docker configuration (Selenium + Chrome + Python dependencies)
├── chrome-installer.sh       # Script to install Chrome/Chromedriver in Lambda environment
├── main.py                   # Lambda handler (entry point for AWS Lambda)
├── scraper.py                # Core parser logic and data extraction
├── process_selenium.py       # Manages anti-scraping pages (uses Selenium WebDriver)
└── README.md                 # Project documentation
```

## Output:

The scraper returns a JSON file containing company data that matches the entered search parameters.