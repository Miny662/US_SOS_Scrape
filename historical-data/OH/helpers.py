#!/usr/bin/env python
# coding: utf8

import os
import json
import datetime
import signal

class Helpers:
    def __init__(self):
        self.STOP_SIGNAL = False
        signal.signal(signal.SIGINT, self.signal_handler)
        self.OUTPUT_DIR = "output"
        self.create_output_dir()

    def create_output_dir(self):
        """Create the output directory"""
        self.create_folder(self.OUTPUT_DIR)

    def signal_handler(self, sig, frame):
        print("\nTermination requested. Saving and exiting...")
        self.STOP_SIGNAL = True

    def date_current(self):
        return (datetime.datetime.now()).strftime("%m-%d-%Y")

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

    def save_to_jsonl(self, data, filepath):
        with open(filepath, "a", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.write("\n")

    def load_checkpoint(self, checkpoint_file):
        try:
            if os.path.exists(checkpoint_file):
                with open(checkpoint_file, "r") as f:
                    return int(f.read().strip())
        except:
            pass
        return 1

    def save_checkpoint(self, pos, checkpoint_file):
        with open(checkpoint_file, "w") as f:
            f.write(str(pos))

    def normalize_item(self, item):
        if item is None:
            return None
        item = str(item).replace("\r", "")
        item = " ".join(item.split())
        item = item.strip()
        return item

    def get_output_path(self, filename):
        """Get the full path for a file in the output directory"""
        return os.path.join(self.OUTPUT_DIR, filename) 