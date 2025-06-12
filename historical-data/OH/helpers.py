#!/usr/bin/env python
# coding: utf8

import re
import os
import datetime
import json
import pandas as pd
from argparse import ArgumentTypeError


class Helpers(object):
    def __init__(self):
        # Create output directory if it doesn't exist
        self.output_dir = "output"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # Set up file paths
        date_str = self.date_current()
        self.jsonl_file = os.path.join(self.output_dir, f"ohio_businesses_{date_str}.jsonl")
        self.csv_file = os.path.join(self.output_dir, f"ohio_businesses_{date_str}.csv")
        self.checkpoint_file = os.path.join(self.output_dir, "checkpoint.json")
        
        # Initialize or load existing data
        self.all_data = self.load_existing_data()

    # get date current
    def date_current(self):
        return (datetime.datetime.now()).strftime("%m-%d-%Y")

    # create new folder
    def create_folder(self, directory_name):
        directory = os.path.isdir(directory_name)
        if directory == False:
            try:
                os.mkdir(directory_name)
            except OSError:
                msg = ("Creation of the directory failed")
            else:
                msg = ("Successfully created the directory")
        folder_path = os.path.realpath(directory_name)
        return folder_path
    
    def clean_item(self, item):
        item = " ".join(item.split())
        item = item.strip()
        return item

    def load_existing_data(self):
        """Load existing data from JSONL file if it exists"""
        data = {
            "metadata": {
                "date_created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_records": 0,
                "last_id": 0
            },
            "data": []
        }

        if os.path.exists(self.jsonl_file):
            try:
                with open(self.jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():  # Skip empty lines
                            record = json.loads(line)
                            data["data"].append(record)
                data["metadata"]["total_records"] = len(data["data"])
                print(f"Loaded {len(data['data'])} existing records from {self.jsonl_file}")
            except Exception as e:
                print(f"Error loading existing data: {e}")
        
        return data

    def save_checkpoint(self, last_id, current_data=None):
        """Save the last processed ID and optionally update data files"""
        try:
            # First update the data files if we have new data
            if current_data is not None and current_data:
                self.update_data(current_data)
            
            # Then update the checkpoint
            self.all_data["metadata"]["last_id"] = last_id
            
            # Save the checkpoint file
            checkpoint_data = {
                "last_processed_id": last_id,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_file": self.jsonl_file,
                "total_records": self.all_data["metadata"]["total_records"]
            }
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2)

            print(f"Progress saved: Last processed ID = {last_id}")
        except Exception as e:
            print(f"Error saving checkpoint: {e}")
            raise

    def load_checkpoint(self):
        """Load the last processed ID from checkpoint file"""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    checkpoint_data = json.load(f)
                last_id = checkpoint_data.get("last_processed_id", 0)
                
                # Verify that the last_id matches what's in our data
                if self.all_data["metadata"].get("last_id", 0) != last_id:
                    print("Warning: Checkpoint and data file last_id mismatch. Using checkpoint value.")
                    self.all_data["metadata"]["last_id"] = last_id
                
                print(f"Resuming from checkpoint: Last processed ID = {last_id}")
                return last_id
            return self.all_data["metadata"].get("last_id", 0)
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return 0

    def update_data(self, new_records):
        """Update the main data files with new records"""
        try:
            # Append new records to JSONL file
            with open(self.jsonl_file, "a", encoding="utf-8") as f:
                for record in new_records:
                    if record:  # Only write non-None records
                        # Add metadata to each record
                        record["_metadata"] = {
                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        f.write(json.dumps(record) + "\n")

            # Update the data in memory
            self.all_data["data"].extend(new_records)
            self.all_data["metadata"]["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.all_data["metadata"]["total_records"] = len(self.all_data["data"])

            # Prepare denormalized data for CSV
            records = []
            for entry in self.all_data["data"]:
                if not entry:
                    continue
                    
                # Get base business info
                base_info = {
                    "business_name": entry.get("business_name", "N/A"),
                    "entity": entry.get("entity", "N/A"),
                    "filing_type": entry.get("filing_type", "N/A"),
                    "original_filing_date": entry.get("original_filing_date", "N/A"),
                    "status": entry.get("status", "N/A"),
                    "expiry_date": entry.get("expiry_date", "N/A"),
                    "source_url": entry.get("source_url", "N/A")
                }

                # If there are no filings, add just the business info
                if not entry.get("filings"):
                    records.append(base_info)
                else:
                    # Add a row for each filing, combined with business info
                    for filing in entry["filings"]:
                        record = base_info.copy()
                        record.update({
                            "filing_type_detail": filing.get("filing_type", "N/A"),
                            "filing_date": filing.get("date_of_filing", "N/A"),
                            "document_id": filing.get("document_id", "N/A")
                        })
                        records.append(record)

            # Save to CSV
            df = pd.DataFrame(records)
            # Reorder columns to put source_url at the end
            columns = [col for col in df.columns if col != 'source_url'] + ['source_url']
            df = df[columns]
            df.to_csv(self.csv_file, index=False)

            print(f"Updated data files with {len(new_records)} new records:")
            print(f"- {self.jsonl_file}")
            print(f"- {self.csv_file}")
            print(f"Total records: {len(self.all_data['data'])}")
        except Exception as e:
            print(f"Error updating data files: {e}")
            raise 