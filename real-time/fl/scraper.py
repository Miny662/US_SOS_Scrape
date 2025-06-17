#!/usr/bin/env python
# coding: utf8

import os
import time
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from process_selenium import ProcessSelenium


class Scraper:
    def __init__(self, id):
        self.id = id
        self.ps = ProcessSelenium()
        self.URL_BASE = "https://search.sunbiz.org/"
        self.URL = urljoin(
            self.URL_BASE, 
            "Inquiry/CorporationSearch/ByDocumentNumber")
    
    def normalize_item(self, item):
        item  = " ".join(item.split())
        return item

    # extract all items from the details page
    def parser_items_details(self, soup):
        items = {}
        keys = ["Document Number", 
                "FEI/EIN Number", 
                "Date Filed", 
                "State", 
                "Status", 
                "Last Event", 
                "Event Date Filed", 
                "Event Effective Date", 
                "Mailing Address", 
                "Registered Agent Name & Address", 
                "Officer/Director Detail",
                "Authorized Person(s) Detail", 
                "Annual Reports"
            ]
        element = soup.select_one("div.searchResultDetail")
        if element:
            name_element = element.select_one("div.detailSection.corporationName")
            if name_element:
                aux = name_element.get_text(strip=True, separator=", ")
                aux = aux.split(",", 1)
                items["Name"] = aux[-1].strip() if aux else ""
                items["Type"] = aux[0].lower().replace(
                    "florida", "").strip().capitalize() if aux else ""
            else:
                items["Name"] = ""
                items["Type"] = ""
            fi_element = element.select_one("div.detailSection.filingInformation")
            if fi_element:
                for fi_element_header in fi_element.select("span div label"):
                    try:
                        index = keys.index(fi_element_header.text.strip())
                    except:
                        pass
                    else:
                        fi_element_value = fi_element_header.find_next_sibling("span")
                        items[keys[index]] = fi_element_value.text.strip() if fi_element_value else ""

            elements = element.select("div.detailSection")
            for element_ in elements:
                element_header = element_.select_one("span")
                try:
                    index = keys.index(element_header.text.strip())
                except:
                    pass
                else:
                    if "Detail" in keys[index]:
                        span_elements = element_.find_all(
                            lambda tag:tag.name=="span" and "Title" in tag.text)
                        items_detail_lst = []
                        for span_element in span_elements:
                            items_detail = {}
                            items_detail["title"] = span_element.text.split("\xa0")[-1].strip()
                            addr = span_element.find_next_sibling("span")
                            if addr:
                                name_ = addr.previous_sibling
                                items_detail["name"] = name_.replace(
                                    "\r", "").replace("\n", "").strip() if name_ else ""
                                addr_ = addr.select_one("div")
                                items_detail["address"] = addr_.get_text(
                                    strip=True, separator=", ") if addr_ else ""
                            items_detail_lst.append(items_detail)
                        items[keys[index]] = items_detail_lst
                    elif keys[index] == "Annual Reports":
                        table = element_.select_one("table")
                        if table:
                            items_detail_report_lst = []
                            rows = table.select("tr")
                            for i, row in enumerate(rows):
                                if i == 0:
                                    cols = [col.text.strip() for col in row.select(
                                        "td.AnnualReportHeader")]
                                else:
                                    cells = row.select("td")
                                    items_detail_report = {}
                                    for cell, col in zip(cells, cols):
                                        items_detail_report[col] = cell.text.strip()
                                    items_detail_report_lst.append(items_detail_report)
                            items[keys[index]] = items_detail_report_lst
                    else:
                        aux = None
                        while True:
                            item_element = element_header.find_next_sibling("span")
                            if item_element:
                                item_value = item_element.select_one("div")
                                if item_value:
                                    if aux:
                                        items[keys[index]] = aux + ", " + item_value.get_text(
                                            strip=True, separator=", ")
                                    else:
                                        items[keys[index]] = item_value.get_text(
                                            strip=True, separator=", ")
                                    break
                                else:
                                    aux = item_element.text.strip()
                                    element_header = item_element
                            else:
                                break

        return items

    # enter the search parameters
    def search(self):
        self.ps.driverBrowser.get(self.URL)        
        search_txt = self.ps.presence_of_element(
            "input#SearchTerm")
        if search_txt:
            search_txt.send_keys(self.id)
            continue_btn = self.ps.presence_of_element(
                'input[type="submit"]')
            if continue_btn:
                continue_btn.click()
                print("Success insert parameters...!!!")
                time.sleep(1)
                return True
        return False

    # start scraper
    def parser(self):
        items = {}
        if self.id:
            self.ps.initialize_drive()
            if self.search():                
                try:
                    soup = BeautifulSoup(
                        self.ps.driverBrowser.page_source, "html.parser")

                    items = self.parser_items_details(soup)
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
            self.ps.close_driver()        
        else:
            result = {"success": False,
                      "message": "Input parameters failure...!!!"
                }
        return result          
