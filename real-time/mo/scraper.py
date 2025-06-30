#!/usr/bin/env python
# coding: utf8

import os
import time
import datetime
import json
from urllib.parse import urljoin, unquote

from bs4 import BeautifulSoup

from process_selenium import ProcessSelenium


class Scraper:
    def __init__(self, id):
        self.id = id
        self.URL_BASE = "https://bsd.sos.mo.gov/"
        self.URL = urljoin(
            self.URL_BASE, "BusinessEntity/BESearch.aspx?SearchType=0")
        self.ps = ProcessSelenium()

    def normalize_item(self, item):
        item = item.replace("\t", "").replace("\r", "")
        item  = " ".join(item.split())
        item = item.strip()
        return item

    def parser_addresses(self):
        addresses = []        
        element = self.ps.presence_of_element('a[tabindex="3"]')
        if element:
            element.click()
            table = self.ps.presence_of_element(
                "table#ctl00_ctl00_ContentPlaceHolderMain_ContentPlaceHolderMainSingle_ppBEDetail_BEAddressGrid_ctl00")
            if table:
                keys = ["type", "Address", "Since", "To"]
                rows = table.find_elements(self.ps.By.CSS_SELECTOR, "tr")
                for row in rows[1:]:
                    items = {}
                    cells = row.find_elements(self.ps.By.CSS_SELECTOR, "td")
                    try:
                        for key, cell in zip(keys, cells[1:]):
                            items[key] = self.normalize_item(cell.text)
                    except:
                        pass
                    if items:
                        addresses.append(items)

        return addresses

    def parser_items_details(self, content):
        items = {}
        keys = {"General Information": [
            "Name", "Type", "Charter No.", "Domesticity",
            "Home State", "Status", "Duration", 
            "Date Formed", "Renewal Month", "Report Due",
                                       ],
        "Registered Agent Information": ["Registered Agent"],
        "Managers": ["Managed by"],
        "Addresses": []
         }
        
        soup = BeautifulSoup(content, "html.parser")
        container = soup.select_one(
            "div#ctl00_ctl00_ContentPlaceHolderMain_ContentPlaceHolderMainSingle_ppBEDetail_pvBEGeneral")
        if container:
            for key, value in keys.items():
                items_details = {}
                if key == "Addresses":
                    items_details = self.parser_addresses()
                for detail_key in value:
                    element = container.find(
                        lambda tag:tag.name=="span" and detail_key in self.normalize_item(tag.text.strip()))
                    if element:
                        parent_element = element.find_parent("div")
                        if parent_element:
                            data_element = parent_element.find_next_sibling("div")
                            if detail_key == "Registered Agent":
                                agent_value = data_element.select_one(
                                    "span#ctl00_ctl00_ContentPlaceHolderMain_ContentPlaceHolderMainSingle_ppBEDetail_lRegAgentValue")
                                items_details[detail_key] = self.normalize_item(agent_value.text) if agent_value else ""
                                address = data_element.select_one("span.swLabelWrap")
                                items_details["Principal Office Address"] = self.normalize_item(address.text) if address else ""
                            else:
                                items_details[detail_key] = self.normalize_item(data_element.text) if data_element else ""
                items[key] = items_details
        return items

    # parser items from web
    def parser_items(self):
        items = {}
        table = self.ps.presence_of_element(
            "table#ctl00_ctl00_ContentPlaceHolderMain_ContentPlaceHolderMainSingle_ppBESearch_bsPanel_SearchResultGrid_ctl00")
        if table:
            rows = table.find_elements(self.ps.By.CSS_SELECTOR, "tr")
            print(len(rows), "@@@@")
            for i, row in enumerate(rows[1:]):
                try:
                    anchor = row.find_element(
                        self.ps.By.CSS_SELECTOR, 
                        'a[title="Select the link to view the Full Details for this Business"]')
                except:
                    pass
                else:
                    if anchor:
                        url = urljoin(self.URL_BASE, anchor.get_attribute("href"))
                        anchor.click()
                        content = self.ps.driverBrowser.page_source
                        items = self.parser_items_details(content)
                        if items:
                            items["page_url"] = url
                            print(items)
                            print("______________________________________________________________________")
                            return items
        return items

    def search(self):
        select_element = self.ps.presence_of_element(
            "select#ctl00_ctl00_ContentPlaceHolderMain_ContentPlaceHolderMainSingle_ppBESearch_bsPanel_ddlBESearchType")
        if select_element:
            select = self.ps.select(select_element)
            select.select_by_value("3")
            time.sleep(1)
            search_txt = self.ps.presence_of_element(
                "input#ctl00_ctl00_ContentPlaceHolderMain_ContentPlaceHolderMainSingle_ppBESearch_bsPanel_tbBusinessID")
            if search_txt:
                search_txt.send_keys(self.id)
                continue_btn = self.ps.presence_of_element(
                    "div#ctl00_ctl00_ContentPlaceHolderMain_ContentPlaceHolderMainSingle_ppBESearch_bsPanel_stdbtnSearch_divStandardButtonTop")
                if continue_btn:
                    continue_btn.click()
                    time.sleep(1)
                    return True
        return False

    # start scraper
    def parser(self):
        items_lst = []
        if self.id:
            self.ps.initialize_driver()
            if self.ps.status_page("//div[@id='main-content']", self.URL):
                if self.search():
                    try:
                        items = self.parser_items()
                    except Exception as e:
                        result = {"success": False,
                                  "message": e 
                            }
                    else:
                        result = {"success": True,
                                  "data": items
                            }
            self.ps.close_driver()
        else:
            result = {"success": False,
                      "message": "Input parameters failure...!!!"
                }
        return result          
