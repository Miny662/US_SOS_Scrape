#!/usr/bin/env python
# coding: utf8

import re
import time
import random
from urllib.parse import urljoin
import json

from bs4 import BeautifulSoup

from process_request import ProcessRequest
from process_selenium import ProcessSelenium


class Scraper:
    def __init__(self, params):
        self.id = params.get("id", None)
        self.pr = ProcessRequest()
        self.ps = ProcessSelenium()
        self.URL_BASE = "https://bizfileonline.sos.ca.gov/"
        self.URL = urljoin(self.URL_BASE, "api/Records/businesssearch")

    # set headers
    def get_headers(self, index, url_refer=None):
        user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
        headers = [
                    {
                        "User-Agent": user_agent,
                        "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "authorization": "undefined",
                        "content-type": "application/json",
                        "Connection": "keep-alive",
                        "Referer": url_refer
                    }
                  ]
        return headers[index]

    def clean_item(self, item):
        item = " ".join(item.split())
        item = item.strip()
        return item

    def normalize_name(self, item):
        item = re.sub(r'\([^)]*\)|^\"', '', item)
        return item.strip()

    def get_record_num(self, item):
        match = re.search(r'\((.*?)\)', item)
        if match:
            return match.group(1)
        return None

    def parser_item_details(self, id, name):
        items = {}
        url = urljoin(self.URL_BASE, "/api/FilingDetail/business/{}/false".format(id))
        self.ps.initialize_driver()
        if self.ps.status_page("//DRAWER", url):
            soup = BeautifulSoup(self.ps.driverBrowser.page_source, "html.parser")
            list_element = soup.select_one("DRAWER_DETAIL_LIST")
            print(list_element, "@@@$$$")
            if list_element:
                elements = list_element.select("DRAWER_DETAIL")
                items["Business Name"] = name
                for element in elements:
                    label = element.select_one("LABEL")
                    label = label.text.strip()
                    value = element.select_one("VALUE")
                    if "Address" in label:
                        # keep new line
                        items[label] = value.text.strip()
                    else:
                        items[label] = self.clean_item(value.text.strip())

        self.ps.close_driver()
        return items

    # parser items from web
    def parser_items(self, response):
        items = {}
        parsed = response.json()
        rows = parsed.get("rows", [])
        for row in rows:
            row_dict = rows[row]
            id = row_dict.get("ID")
            print(id, "***")
            print(row_dict, "***")
            record_num = None
            try:
                orginal_name = row_dict.get("TITLE", [])[0]
                record_num = self.get_record_num(orginal_name)
                name = self.normalize_name(orginal_name)
            except:
                name = ""
            if record_num and self.id == record_num:
                print("DAMPAAAAAAAAAAAAA")
                items = self.parser_item_details(id, name)
                print(items, "+++")
                return items
        return items

    def get_params(self):
        params =  {"SEARCH_VALUE": self.id,
                   "SEARCH_FILTER_TYPE_ID": "0",
                   "SEARCH_TYPE_ID": "1",
                   "FILING_TYPE_ID": "",
                   "STATUS_ID": "",
                   "FILING_DATE": {"start": None, "end": None},
                   "CORPORATION_BANKRUPTCY_YN": False,
                   "CORPORATION_LEGAL_PROCEEDINGS_YN": False,
                   "OFFICER_OBJECT": {"FIRST_NAME": "", "MIDDLE_NAME": "", "LAST_NAME": ""},
                   "NUMBER_OF_FEMALE_DIRECTORS": "99",
                   "NUMBER_OF_UNDERREPRESENTED_DIRECTORS": "99",
                   "COMPENSATION_FROM": "",
                   "COMPENSATION_TO": "",
                   "SHARES_YN": False,
                   "OPTIONS_YN": False,
                   "BANKRUPTCY_YN": False,
                   "FRAUD_YN": False,
                   "LOANS_YN": False,
                   "AUDITOR_NAME": ""}
        return params

    # start scraper
    def parser(self):
        if self.id:
            response = self.pr.set_request(
                self.URL,
                headers=self.get_headers(0, urljoin(self.URL_BASE, "search/business/")),
                params=self.get_params())

            if response:
                try:
                    items = self.parser_items(response)
                except Exception as e:
                    print("Error: {}".format(e))
                    result = {"success": False,
                              "message": "Parser error...!!!"
                        }
                else:
                    result = {"success": True,
                              "data": items
                        }
            else:
                result = {"success": False,
                          "message": "Error connecting to the web...!!!"
                    }
        else:
            result = {"success": False,
                      "message": "Input parameters failure...!!!"
                }

        return result
