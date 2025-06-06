#!/usr/bin/env python
# coding: utf8

import sys
import time

import requests
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
import urllib3


class ProcessRequest(object):
    def __init__(self):
        self.session = requests.Session()
        self.session.cookies.clear()

    # msg script abruptly terminated        
    def script_terminated(self, msg):
        print("___________________________________________________________________________________")
        print("Number of failed attempts. Script abruptly terminated...due to the following error:")
        print("___________________________________________________________________________________")
        print(msg)
        sys.exit()

    # retry 
    def retry(self, n):
        N_ATTEMPS = 150
        WAIT_TIME = 3
        print("reconnecting...", flush=True)
        time.sleep(WAIT_TIME)
        return False if n == N_ATTEMPS else True

    # set request
    def set_request(self, url, params=None, headers=None, verify=None, cookies=None):
        count = 0
        loop = True
        while loop:
            try:
                if params is None:
                    print(cookies, "@@@")
                    response = self.session.get(url, timeout=60, headers=headers, cookies=cookies)
                else:
                    response = self.session.post(url, json=params, timeout=60, headers=headers, cookies=cookies)
                response.raise_for_status()
                loop = (response.status_code != 200)
            except requests.exceptions.HTTPError as httpErr: 
                msg = "Http Error: ", httpErr
                self.session.cookies.clear()
                if response.status_code == 404:
                    return False
            except requests.exceptions.ConnectionError as connErr: 
                msg = "Error Connecting: ", connErr
            except requests.exceptions.Timeout as timeOutErr: 
                msg = "Timeout Error: ", timeOutErr
                return None
            except requests.exceptions.RequestException as reqErr: 
                msg = "Something Else: ", reqErr 
            if loop:
                print(msg)
                count = count + 1
                if not self.retry(count):
                    self.script_terminated(msg)

        return response