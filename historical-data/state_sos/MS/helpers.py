import os
import re
import logging
import json

def clean_text(text):
    """Clean text by removing extra whitespace and normalizing."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def get_data_files(directory):
    """Get all data files in the directory, sorted by start ID."""
    files = [f for f in os.listdir(directory) if f.startswith("data_ids_") and f.endswith(".jsonl")]
    def extract_start_id(filename):
        parts = filename.split("_")
        try:
            return int(parts[2])
        except:
            return 0
    files.sort(key=extract_start_id)
    return [os.path.join(directory, f) for f in files]

def load_range_progress(progress_file, start_id):
    """Load progress from a progress file."""
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_id", start_id - 1)
        except Exception as e:
            logging.warning(f"Could not read progress file {progress_file}: {e}")
    return start_id - 1

def save_range_progress(progress_file, last_id):
    """Save progress to a progress file."""
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump({"last_id": last_id}, f) 