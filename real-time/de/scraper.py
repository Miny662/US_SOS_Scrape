#!/usr/bin/env python
# coding: utf8

import os
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from process_request import ProcessRequest


class Scraper:
    def __init__(self, id):
        self.id = id
        
        self.pr = ProcessRequest()
       
        self.URL_BASE = "https://icis.corp.delaware.gov/"
        self.URL = urljoin(self.URL_BASE, "Ecorp/EntitySearch/NameSearch.aspx")
        self.SITE_KEY = "6Le1dNQZAAAAAGYNA9djIXojESuOKtvMLtRoga3r"

        self.STATE = "delaware"

    # set headers
    def get_headers(self, index, url_refer=None):
        user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
        headers = [
                    {
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br"
                    },
                    {
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Connection": "keep-alive",
                        "Referer": url_refer

                    }
                  ] 
        return headers[index]

    def get_params(self, response, target=None):
        params = {}
        if target is None:
            params = {
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": "",
                    "__VIEWSTATEGENERATOR": "",
                    "ctl00$hdnshowlogout": "",
                    "ctl00$hdnfilingtype": "",
                    "as_sitesearch": "",
                    "ctl00$ContentPlaceHolder1$frmEntityName": "",
                    "ctl00$ContentPlaceHolder1$frmFileNumber": self.id,
                    "ctl00$ContentPlaceHolder1$hdnPostBackSource": "",
                    "ctl00$ContentPlaceHolder1$lblMessage": "",
                    "email_confirm": "",
                    "ctl00$ContentPlaceHolder1$btnSubmit": "Search",
                    "ctl00$ContentPlaceHolder1$hdnNavigation": ""
            }
        else:
            params = {
                    "__EVENTTARGET": target,
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": "",
                    "__VIEWSTATEGENERATOR": "",
                    "ctl00$hdnshowlogout": "",
                    "ctl00$hdnfilingtype": "",
                    "as_sitesearch": "",
                    "ctl00$ContentPlaceHolder1$frmEntityName": "",
                    "ctl00$ContentPlaceHolder1$frmFileNumber": self.id,
                    "ctl00$ContentPlaceHolder1$hdnPostBackSource": "",
                    "ctl00$ContentPlaceHolder1$lblMessage": "",
                    "email_confirm": "",
                    "ctl00$ContentPlaceHolder1$hdnNavigation": ""
            }

            soup = BeautifulSoup(response.content, "html.parser")
            keys = ("__VIEWSTATE", "__VIEWSTATEGENERATOR")
            for key in keys:
                element = soup.select_one("input#{}".format(key))
                params[key] = element["value"] if element else ""
            
        return params

    def normalize_name(self, item):
        item = re.sub(r'\([^)]*\)|^\"', '', item)
        return item.strip()

    def parser_item_details(self, params):
        response = self.pr.set_request(
            self.URL,
            headers=self.get_headers(1, self.URL),
            params=params)
        items = {}
        if response:
            keys = {"General Information": {"File Number": "ctl00_ContentPlaceHolder1_lblFileNumber",
                                            "Entity Name": "ctl00_ContentPlaceHolder1_lblEntityName",
                                            "Incorporation Date/Formation Date": "ctl00_ContentPlaceHolder1_lblIncDate",
                                            "Entity Kind": "ctl00_ContentPlaceHolder1_lblEntityKind",
                                            "Entity Type": "ctl00_ContentPlaceHolder1_lblEntityType",
                                            "Residency": "ctl00_ContentPlaceHolder1_lblResidency",
                                            "State": "ctl00_ContentPlaceHolder1_lblState",
                                           },
            "Registered Agent Information": {"Name": "ctl00_ContentPlaceHolder1_lblAgentName",
                                             "Address": "ctl00_ContentPlaceHolder1_lblAgentAddress1",
                                             "City": "ctl00_ContentPlaceHolder1_lblAgentCity",
                                             "County": "ctl00_ContentPlaceHolder1_lblAgentCounty",
                                             "State": "ctl00_ContentPlaceHolder1_lblAgentState",
                                             "Postal Code": "ctl00_ContentPlaceHolder1_lblAgentPostalCode",
                                             "Phone": "ctl00_ContentPlaceHolder1_lblAgentPhone",
                                            },
             }
        
            soup = BeautifulSoup(response.content, "html.parser")
            for key, value in keys.items():
                items_ = {}
                for key_, css_selector in value.items():
                    element = soup.select_one("span#{}".format(css_selector))
                    items_[key_] = element.text.strip() if element else ""
                items[key] = items_
        return items

    # parser items from web
    def parser_items(self, response):
        flag = False
        soup = BeautifulSoup(response.content, "html.parser")
        
        table = soup.select_one("table#tblResults")
        if table:
            rows = table.select("tr")
            for limit, row in enumerate(rows[1:], 1):
                element = row.select_one("td a")
                if element:
                    aux = element["href"]
                    target = aux.split(
                        "javascript:__doPostBack('")[-1].split("'")[0]
                    params =self.get_params(response, target)
                    items = self.parser_item_details(params)
                    yield items

    # start scraper
    def parser(self):
        result = {}
        items = {}
        if self.id:
            print(self.id, "***")
            response = self.pr.set_request(
                self.URL, headers=self.get_headers(0))
            if response:
                params =self.get_params(response)
                response = self.pr.set_request(
                    self.URL,
                    headers=self.get_headers(1, self.URL),
                    params=params)

                if response:
                    try:
                        for items in self.parser_items(response):
                            items["page_url"] = self.URL
                            break

                    except Exception as e:
                        print("Error: ", e)
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