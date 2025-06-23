#!/usr/bin/env python
# coding: utf8

import os
import re
import time
import json
import random
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import jsonlines

from process_request import ProcessRequest
from solve_recaptcha import SolveRecaptcha
from helpers import Helpers
from state_sos.base_scraper import BaseScraper


class Scraper(BaseScraper):
    def __init__(self, start_id: int = 1, end_id: int = 11000000):
        super().__init__(start_id, end_id)
        self.file_number = None
        
        self.pr = ProcessRequest()
        self.helpers = Helpers()
        
        self.FOLDER = self.helpers.create_folder("jsonl_out")
        self.DATE = self.helpers.date_current()
        
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

    # output jsonline       
    def jsonl_out(self, items):
        self.DATE = self.helpers.date_current()       
        file_name = "{}_{}.jsonl".format(self.STATE, self.DATE)
        with jsonlines.open( os.path.join(self.FOLDER, file_name), mode ='a') as writer:
            writer.write(items)    

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
                    "ctl00$ContentPlaceHolder1$frmFileNumber": self.file_number,
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
                    "ctl00$ContentPlaceHolder1$frmFileNumber": self.file_number,
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
            
            #print(json.dumps(params, indent=4))
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
        recaptcha = soup.select_one("form")
        if recaptcha and "Please complete the reCAPTCHA" in recaptcha.text:
            print("ANELCAAAAAAAAAAAAAAAAAAAAAAAA")
            g_response = SolveRecaptcha().get_captcha_response(
                    self.URL, 
                    self.SITE_KEY)
            if g_response:
                params = {
                    "g-recaptcha-response": g_response
                }
                response = self.pr.set_request(
                    self.URL,
                    headers=self.get_headers(1, self.URL),
                    params=params)
                
                if response:
                    params =self.get_params(response)
                    response = self.pr.set_request(
                        self.URL,
                        headers=self.get_headers(1, self.URL),
                        params=params)
                    if response:
                        print("DAMPAAAAAAAAAAAAAAAAAAAAA...!!!")
                        soup = BeautifulSoup(response.content, "html.parser")
                        flag = True
        else:
            flag = True

        print(flag, "$$$$$$$")
        if flag:
            table = soup.select_one("table#tblResults")
            if table:
                rows = table.select("tr")
                for limit, row in enumerate(rows[1:], 1):
                    element = row.select_one("td a")
                    if element:
                        aux = element["href"]
                        target = aux.split("javascript:__doPostBack('")[-1].split("'")[0]
                        print(target, "@@@@@@@@@@@@@")
                        params =self.get_params(response, target)
                        items = self.parser_item_details(params)
                        yield items

    # start scraper
    def run(self):
        result = {}
        n = 1
        for self.file_number in range(self.START_ID, self.END_ID):
            print(self.file_number, "***")
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
                            self.jsonl_out(items)
                            print(items)
                            print("*" *75)
                            print(n, "###")
                            n = n + 1
                            time.sleep(random.randint(2, 4))

                    except Exception as e:
                        print("CULOOOOO: ", e)
                        result = {"success": False,
                                  "message": "Parser error...!!!" 
                            }
                    else:
                        result = {"success": True,
                                  "data": "" 
                            }
                else:
                    result = {"success": False,
                              "message": "Error connecting to the web...!!!"
                        }
        else:
            result = {"success": False,
                      "message": "Input parameters failure...!!!"
                }            

        #return result
    

if __name__ == "__main__":
    Scraper().run()
