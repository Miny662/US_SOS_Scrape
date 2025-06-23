#!/usr/bin/env python
# coding: utf8

import re
import os
import datetime
from argparse import ArgumentTypeError


class Helpers:
    def __init__(self):
        pass

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
    
    def normalize_item(self, item):
        item = item.replace("\r", "")
        item = " ".join(item.split())
        item = item.strip()
        return item
