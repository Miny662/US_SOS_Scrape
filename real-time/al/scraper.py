#!/usr/bin/env python
# coding: utf8

import os
from urllib.parse import urljoin
import json

from bs4 import BeautifulSoup

from process_request import ProcessRequest 


class Scraper:
    def __init__(self, id):
        self.pr = ProcessRequest()

        self.URL_BASE = "https://arc-sos.state.al.us/"

        self.STATE = "alabama"

        self.id = id

    def get_headers(self, index, url_refer=None):
        user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
        headers = [
                    {
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                    },
                    {
                        "User-Agent": user_agent,
                        "Accept": "application/json, text/plain, */*",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Content-Type": "application/json;charset=utf-8",
                        "Referer": "https://apps.dos.ny.gov/publicInquiry/EntityDisplay"
                    },
                    {
                        "User-Agent": user_agent,
                        "Accept": "application/json, text/plain, */*",
                        "Content-Type": "application/json;charset=utf-8",
                        "Referer": "https://apps.dos.ny.gov/publicInquiry/AssumedNameHistory"
                    }
        ]
        return headers[index]

    def get_params(self, index, entity_name=None):
        params = [ 
            {
                "searchValue": self.id,
                "searchByTypeIndicator": "DosID",
                "searchExpressionIndicator": "BeginsWith",
                "entityStatusIndicator": "AllStatuses",
                "entityTypeIndicator": [
                    "Corporation", 
                    "LimitedLiabilityCompany", 
                    "LimitedPartnership", 
                    "LimitedLiabilityPartnership"],
                "listPaginationInfo": {"listStartRecord": 1, "listEndRecord": 50}
            },
            {
                "AssumedNameFlag":"false",
                "SearchID": self.id,
            },
            {
                "SearchID": self.id,
                "AssumedNameFlag": "false",
                "ListSortedBy": "ALL",
                "listPaginationInfo": {"listStartRecord": 1, "listEndRecord": 50}
            }
        ]

        return params[index]

    def normalize_item(self, item):
        item  = " ".join(item.split())
        item = item.strip()
        return item

    def parser_items_details(self, response):
        keys = {"General Information": ["Entity Name", "Entity ID Number", "Entity Type", "Principal Address", "Principal Mailing Address", "Status", "Merged Date", "Merged Into", "Place of Formation", 
                                        "Formation Date", "Qualify Date", "Registered Agent Name", "Registered Office Street Address", "Registered Office Mailing Address",
                                        "Nature of Business", "Doing Business in AL Since", "Capital Authorized", "Capital Paid In"],
                "Organizers": ["Organizer Name", "Organizer Street Address", "Organizer Mailing Address"],
                "Members": ["Member Name", "Member Street Address", "Member Mailing Address"],
                "Directors": ["Director Name", "Director Street Address", "Director Mailing Address"],
                "Incorporators": ["Incorporator Name", "Incorporator Street Address", "Incorporator Mailing Address"],
                "Transactions": ["Transaction Date"],
                "Scanned Documents ": ["Document Date / Type / Pages"]
            }
        soup = BeautifulSoup(response.content, "html.parser")
        items = {}        
        for key, value in keys.items():
            if key == "General Information":
                items_ = {}
                for item in value:
                    if item == "Entity Name":
                        entity_name = soup.select_one("table thead tr td.aiSosDetailHead")
                        if entity_name is None:
                            return {}
                        items_[item] = entity_name.text.strip() if entity_name else ""
                    else:
                        element = soup.find("td", string="{}".format(item))
                        if element:
                            data_element = element.find_next_sibling("td")
                            items_[item] = data_element.text.strip() if data_element else ""
                        else:
                            items_[item] = "" 
                items[key] = items_
            elif key == "Transactions":
                total_items = []
                elements = soup.find_all("td", string="{}".format("Transaction Date"))
                for element in elements:
                    items_ = {}
                    data_element = element.find_next_sibling("td")
                    if data_element:
                        items_["Transaction Date"] = self.normalize_item(data_element.text)
                        row_parent = element.find_parent("tr")
                        if row_parent:
                            next_row = row_parent.find_next_sibling("tr")
                            if next_row:
                                key_element = next_row.select_one("td.aiSosDetailDesc")
                                if key_element:
                                    data_element_ = key_element.find_next_sibling("td")
                                    items_[key_element.text.strip()] = self.normalize_item(
                                        data_element_.text) if data_element_ else ""
                                    total_items.append(items_)
                if total_items:
                    items[key] = total_items
                else:
                    items[key] = {"Transaction Date": ""}
            else:
                total_items = []
                full_items = []
                for item in value:
                    elements = soup.find_all("td", string="{}".format(item))
                    lst_items = []
                    for element in elements:
                        data_element = element.find_next_sibling("td")
                        if data_element:
                            lst_items.append(
                                {item: self.normalize_item(data_element.text)})
                    if lst_items:
                        total_items.append(lst_items)
                    else:
                        lst_items.append({item: ""})
                        total_items.append(lst_items)
                
                for i in range(len(total_items[0])):
                    items_ = {}
                    for aux_item in total_items:
                        items_ = {**items_, **aux_item[i]}
                    full_items.append(items_)
                items[key] = full_items
        print(items)
        print("________________________________________________________________________________________________________________")       
        return items

    def parser(self):        
        if self.id:
            query_string = f"cgi/corpdetail.mbr/detail?page=number&corp={self.id}"
            url = urljoin(self.URL_BASE, query_string)
            response = self.pr.set_request(
                url, 
                headers=self.get_headers(0)
            )
            if response:
                try:
                    items = self.parser_items_details(response) 
                except:
                    result = {
                        "success": False,
                        "message": "Parser error...!!!" 
                    }
                else:
                    result = {
                        "success": True,
                        "data": items
                    }
            else:
                result = {
                    "success": False,
                    "message": "Error connecting to the web...!!!"
                }
        else:
            result = {
                "success": False,
                "message": "Input parameters failure...!!!"
            }                    

        return result