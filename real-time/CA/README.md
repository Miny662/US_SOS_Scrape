### Scraper Real Time palm-realtime-ca:

Real-Time Scraper for California Secretary of State (SOS California) Business Search

This project features a scraper designed specifically for conducting real-time searches on the California Secretary of State (SOS California) website. Its primary function is to extract business information using the company's identification number (Business ID).

🚀 Automated Selenium Scraper on AWS Lambda (Containerized)
Deploy a Python + Selenium scraper as a serverless Lambda function using Docker.

📋 Prerequisites
AWS CLI configured with IAM/SSO credentials

Docker installed

Python 3.9+

AWS permissions for:

ECR (Elastic Container Registry)

Lambda

IAM (execution roles)

🛠️ Quick Start

1. Build & Push Docker Image

# Build image
docker build -t palm-selenium-chrome-driver .

# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 430118818332.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag palm-selenium-chrome-driver:latest 430118818332.dkr.ecr.us-east-1.amazonaws.com/palm-selenium-chrome-driver:latest
docker push 430118818332.dkr.ecr.us-east-1.amazonaws.com/palm-selenium-chrome-driver:latest

🏗️ Project Structure


├── Dockerfile                # Docker config (Selenium + Chrome)
├── main.py                   # Lambda handler
├── scraper.py                # parser logic
├── process_request.py        # Handling initial requests with requests
├── process_selenium.py       # Handling detail page requests with Selenium as it has an anti-web scraping mechanism
└── README.md

## Output:

The scraper returns a JSON file containing company data that matches the entered search parameters.