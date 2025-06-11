#!/usr/bin/env python
# coding: utf8

import re
import os
import datetime


class Helpers(object):
    def __init__(self):
        pass

    # get date current
    def date_current(self):
        return (datetime.datetime.now()).strftime("%m-%d-%Y")
    
    def normalize_item(self, item):
        item = item.replace("\r", "")
        item  = " ".join(item.split())
        item = item.strip()
        return item
