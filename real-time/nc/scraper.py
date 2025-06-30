#!/usr/bin/env python
# coding: utf8

import os
import time
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from process_request import ProcessRequest


class Scraper:
    def __init__(self, id):
        self.id = id
        self.prequest = ProcessRequest()
        self.URL_BASE = "https://www.sosnc.gov/"
        self.URL = urljoin(
            self.URL_BASE, 
            "online_services/search/Business_Registration_Results")

    # set headers for requests
    def get_headers(self, index, url_refer=None):
        user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
        headers = [
                    {
                        "User-Agent": user_agent,
                    },
                    {
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Referer": url_refer,
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "same-origin",
                        "Sec-Fetch-User": "?1",
                        "Priority": "u=0, i",
                        "TE": "trailers"
                    },
                    {
                        "User-Agent": user_agent,
                        "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Referer": url_refer,
                        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                        "X-Requested-With": "XMLHttpRequest",
                        "Connection": "keep-alive",
                        "Sec-Fetch-Dest": "empty",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Site": "same-origin",
                        "Priority": "u=0"
                    },
                    {
                        "User-Agent": user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Referer": url_refer,
                        "Connection": "keep-alive",
                        "Upgrade-Insecure-Requests": "1",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "same-origin",
                        "Sec-Fetch-User": "?1",
                        "Priority": "u=0, i"
                    }
                  ] 
        return headers[index]

    # clean item
    def normalize_item(self, item):
        item = item.replace("\r", "")
        item  = " ".join(item.split())
        item = item.strip()
        return item

    # extract all items from the detail page
    def parser_items_details(self, url):
        total_items = {}
        keys = {
            "General Information": [
                "Legal name", "SosId", "Status", "Date Formed", "Citizenship", "Fiscal Month", 
                "Annual Report Due Date", "Annual Report Status", "Registered Agent"],
            "Addresses": ["mailing address", "Principal office address", 
                "Registered office address", "Registered mailing address"],
            "Company Officials": [],
        }
       
        response = self.prequest.set_request(
            url,
            headers=self.get_headers(3, self.URL))
        if response:
            soup = BeautifulSoup(response.content, "html.parser")
            container = soup.select_one(
                "section.usa-section.usa-section--singleEntry")
            if container:
                for key, fields in keys.items():
                    if key == "General Information":
                        items = {}
                        for field in fields:
                            label = field.lower()
                            element = container.find(
                                lambda tag:tag.name=="span" and label in tag.text.strip().lower())
                            if element:
                                if field == "Registered Agent":
                                    next_element = element.find_next_sibling("a")
                                    value = next_element.text if next_element else "" 
                                else:
                                    value = element.next_sibling                            
                                items[field] = self.normalize_item(value)
                            else:
                                items[field] = ""
                        total_items[key] = items
                    elif key == "Addresses":
                        items = {}
                        for field in fields:
                            label = field.lower()
                            element = container.find(
                                lambda tag:tag.name=="span" and label==self.normalize_item(
                                    tag.text).lower())
                            if element:
                                next_element = element.find_next_sibling("div")
                                value = next_element.get_text(
                                    strip=True, separator=" ") if next_element else "" 
                                items[field] = self.normalize_item(value)
                            else:
                                items[field] = ""
                        total_items[key] = items
                    else:
                        items = []
                        ul_element = container.select_one("ul")
                        if ul_element:                            
                            li_elements = ul_element.select("li")
                            for li_element in li_elements:
                                officials = {}
                                title_element = li_element.select_one("span.boldSpan")
                                officials["title"] = self.normalize_item(
                                    title_element.text) if title_element else ""
                                divs_elements = li_element.select("div.para-small")
                                for div_element in divs_elements:
                                    name_element = div_element.select_one("a")
                                    if name_element:
                                        officials["Name"] = self.normalize_item(
                                            name_element.text)
                                    else:
                                        officials["Address"] = self.normalize_item(
                                            div_element.text)
                                items.append(officials)
                        total_items[key] = items

        return total_items

    # parser items from web
    def parser_items(self, response):
        items = {}
        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.select_one("section#resultsSection")
        if table:
            rows = table.select(
                "div.usa-accordion__content.usa-prose.resultsBox.searchAccordion__content")
            for row in rows:
                element = row.find(
                    lambda tag:tag.name=="a" and "More information" in tag.text)
                if element:
                    url = urljoin(self.URL_BASE, element["href"])
                    items = self.parser_items_details(url)
                    print(items)
                    print("*" *75)
                    return items
        return items

    # payload for POST request
    def get_params(self):
        url = urljoin(
            self.URL_BASE, 
            "online_services/search/by_title/search_Business_Registration")
        response = self.prequest.set_request(
            url,
            headers=self.get_headers(0))
        soup = BeautifulSoup(response.content, "html.parser")
        element = soup.select_one('input[name="__RequestVerificationToken"]')
        token = None
        if element:
            token = element["value"]
        params = {
                "__RequestVerificationToken": token,
                "CorpSearchType": "SOSID",
                "EntityType": "ORGANIZATION",
                "Words": "STARTING",
                "SearchCriteria": self.id,
                "IndividualsSurname": "",
                "FirstPersonalName": "",
                "AdditionalNamesInitials": ""
        }
        return params

    # start scraper
    def parser(self):
        if self.id:
            response = self.prequest.set_request(
                self.URL,
                headers=self.get_headers(
                    1, 
                    urljoin(
                        self.URL_BASE, 
                        "online_services/search/by_title/_Business_Registration")),
                params=self.get_params())
            if response:
                try:
                    items = self.parser_items(response)
                except:
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
