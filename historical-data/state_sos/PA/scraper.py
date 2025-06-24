#!/usr/bin/env python
# coding: utf8

import os
import time
import json
import re
from urllib.parse import urljoin

import jsonlines

from .process_request import ProcessRequest
from .helpers import Helpers
from state_sos.base_scraper import BaseScraper


class Scraper(BaseScraper):
    def __init__(self, start_id: int = 1, end_id: int = 3000000):
        super().__init__(start_id, end_id)
        self.prequest = ProcessRequest()

        self.helpers = Helpers()
        
        self.FOLDER = self.helpers.create_folder("jsonl_out")
        self.DATE = self.helpers.date_current()

        self.URL_BASE = "https://file.dos.pa.gov/"
        self.URL = urljoin(self.URL_BASE, "search/business")
        self.URL_POST = urljoin(self.URL_BASE, "api/Records/businesssearch")
        self.STATE = 'pennsylvania'
        self.state_code = 'pa'

    # set headers
    def get_headers(self, index, url_refer=None):
        user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
        headers = [
                    {
                        "User-Agent": user_agent,
                    },
                    {
                        "User-Agent": user_agent,
                        "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Referer": url_refer,
                        "content-type": "application/json",
                        "Connection": "keep-alive"
                    },
                    {
                        "User-Agent": url_refer,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
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

    def parser_items_details(self, id_, main_items):
        keys = {"Business Entity Details": {
                    "Name": "Name",
                    "Former Name": "Formed Name",
                    "Entity Number": "Entity Number", 
                    "Filing Date": "Initial Filing Date",
                    "Entity Type": "Filing Type", 
                    "Entity Subtype": "Filing Subtype",
                    "Status": "Status",
                    "Formed In": "Formed In",
                    "Address": "Principal Address",
                    "Citizenship": "Citizenship",
                    "State Of Inc": "tate Of Inc",
                    "Effective Date": "Effective Date",
                    "Entity Creation Date": "Entity Creation Date",
                    "Registered Office": "Registered Office",
                    "Owner": "Interested Individuals"},
                "Officers": {
                    "Officers": "Officers"
                }
            }
        url = urljoin(
            self.URL_BASE, 
            "api/FilingDetail/business/{}/false".format(id_))
        response = self.prequest.set_request(
                url,
                headers=self.get_headers(1, self.URL))
        items = {}
        if response:
            try:
                parsed = response.json()
            except:
                pass
            else:
                rows = parsed.get("DRAWER_DETAIL_LIST")
                if rows:
                    for key in keys:                
                        items_ = {}
                        for item_key, item_value in keys[key].items():
                            if "Name" in item_key or "Number" in item_key:
                                items_[item_key] = main_items[item_key]
                            else:    
                                for row in rows:
                                    others_key = ("Title", "Name", "Address")
                                    label = row.get("LABEL")
                                    if label == item_value:
                                        if item_key == "Officers":
                                            officers = []                                            
                                            aux_value = row.get("VALUE", "")                                             
                                            if aux_value:                                                                                             
                                                for aux in aux_value.split("\n\n"):
                                                    if aux.strip():
                                                        aux_lst = aux.split("\n")
                                                        i = 0
                                                        items_aux = {}
                                                        for other_key, other_aux in zip(others_key, aux_lst):
                                                            if other_key == "Address":
                                                                items_aux[other_key] = self.helpers.normalize_item(
                                                                    " ".join(aux_lst[i:]))
                                                            else:
                                                                items_aux[other_key] = self.helpers.normalize_item(
                                                                    other_aux.strip())
                                                            i += 1
                                                    officers.append(items_aux)
                                                items_ = officers                                                    
                                        else:    
                                            items_[item_key] = self.helpers.normalize_item(
                                                row.get("VALUE", ""))
                                        break
                                    else:
                                        if item_key != "Officers":
                                            items_[item_key] = ""  
                                        else: 
                                            items_ = [{other_key: "" for other_key in others_key}]
                        items[key] = items_
                    
                    for key in keys:    
                        if key not in items:
                            items[key] = []    
        if items:
            items["page_url"] = url
        return items

    def parser_entity_number(self, item):
        regex = r'(?<=\()\d{1,}(?=\))' 
        matches = re.finditer(regex, item, re.MULTILINE)
        for match in matches:
            item_match = match.group()
            return item_match
        return ""

    def normalize_name(self, name):
        name = name.split("(")[0].strip()
        return name

    # parser items from web
    def parser_items(self, response, id):
        try:
            parsed = response.json()
        except:
            pass
        else:
            rows = parsed.get("rows")
            if rows:
                for limit, row, in enumerate(rows, 1):                    
                    value = rows[row] 
                    other_id = value.get("ID")
                    if other_id: 
                        record_num = value.get("RECORD_NUM")
                        if record_num and int(record_num)==id:                                           
                            name = " ".join(value.get("TITLE", ""))
                            name = name.strip()
                            former_name = ""                        
                            if "Former Name" in name:                        
                                aux_split = name.split("Former Name:")
                                name = aux_split[0].strip()
                                former_name = aux_split[-1].strip()                        
                            main_items = {}
                            main_items["Name"] = self.normalize_name(name)
                            main_items["Former Name"] = former_name
                            main_items["Entity Number"] = self.parser_entity_number(name)
                            items = self.parser_items_details(other_id, main_items)
                            if items:
                                yield items
                                break

    # start scraper
    def run(self):
        n = 0
        for id in range(self.START_ID, self.END_ID):
            print(id, "****")
            params = {
                "SEARCH_VALUE": str(id),
                "SEARCH_FILTER_TYPE_ID": "1",
                "FILING_TYPE_ID": "",
                "STATUS_ID": "",
                "FILING_DATE": {"start": None, "end": None}
            }
            response = self.prequest.set_request(
                self.URL_POST,
                headers=self.get_headers(1, self.URL),
                params=params)
            if response:
                try:
                    for items in self.parser_items(response, id):                        
                        print(n, "###")
                        n = n + 1
                        self.write_to_s3(items, id)
                        print(items)
                        print("*" *75)
                        time.sleep(1)
                except:
                    items = {"success": False,
                              "message": "Parser error...!!!" 
                        }
                else:
                    items = {"success": True,
                              "data": "" 
                        }
            else:
                items = {"success": False,
                          "message": "Error connecting to the web...!!!"
                    }
                

if __name__ == "__main__":
    Scraper().run()
