### Scraper Real Time palm-realtime-nc:

Real-Time Scraper for Nort Carolina Secretary of State (SOS Nort Carolina) Business Search

This project features a scraper designed specifically for conducting real-time searches on the Nort Carolina Secretary of State (SOS Nort Carolina) website. Its primary function is to extract business information using the company's identification number (Business ID).

🚀 Automated Scraper on AWS Lambda
Deploy a Python scraper as a serverless Lambda function.

📋 Prerequisites

Python 3.9+

🛠️ Quick Start

Automatic deployment process in an AWS Lambda function


## 🏗️ Project Structure

```text
.
├── lambda_function.py                   # Lambda handler (entry point for AWS Lambda)
├── scraper.py                # Core parser logic and data extraction
├── process_request.py       # Manages anti-scraping pages (uses Selenium WebDriver)
└── requirements.txt                 # Project dependencies
```

## Output:

The scraper returns a JSON file containing company data that matches the entered search parameters.