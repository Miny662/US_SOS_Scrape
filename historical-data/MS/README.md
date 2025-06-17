# 🕵️ Business ID Scraper for Mississippi Secretary of State (SOS)

This project scrapes business registration data from the Mississippi Secretary of State website using direct API requests.

It supports:
- 🔁 Concurrent scraping with **100 rotating proxies**
- 📌 Automatic **progress tracking and resuming**
- 🧹 Data **cleaning** and **structured JSONL** output
- 📦 Merging partial data into a **single, sorted dataset**
- 🧼 **Auto-cleanup** of intermediate files after completion

---

## 📌 Features

- 🔄 **Concurrent scraping** using 100 Webshare proxies
- 📈 **Workload distributed evenly** across proxies
- ♻️ **Progress saved per proxy**, allowing resume on failure
- 🧽 **Cleaned data** output (removes whitespace/formatting noise)
- 📑 **Merges all partial files** into one final sorted `JSONL`
- 🗑️ **Deletes** all intermediate files after final merge

---

## 🧰 Requirements

- Python **3.8+**
- Dependencies listed in [`requirements.txt`](./requirements.txt)

---

## ⚙️ Setup Instructions

1. Add your proxy file
Place your proxy list in the root directory as:

Webshare 1000 proxies - option 1.txt
Each line should follow this format:

host:port:user:password

2. (Optional) Create a virtual environment

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

3. Install dependencies

pip install -r requirements.txt

▶️ Usage
Run the script:


python scraper.py
The script will:

🔀 Select 100 random proxies from your list

🧾 Scrape business data for IDs from 650001 to 1,114,681

💾 Save per-proxy JSONL files in Output/

✅ Track progress and resume automatically if interrupted

📂 Merge all partial files into Output/merged_data.jsonl

🧹 Delete all progress and partial files after merging