#!/usr/bin/env python
# coding: utf8

import os
from urllib.parse import urljoin

import jsonlines

from .process_request import ProcessRequest
from .helpers import Helpers


class Scraper:
    def __init__(self):
        self.pr = ProcessRequest()
        self.helpers = Helpers()
        
        self.FOLDER = self.helpers.create_folder("jsonl_out")

        self.URL_BASE = "https://apps.dos.ny.gov"

        self.STATE = "new_york"
        self.START_ID = 1
        self.END_ID = 7800000

    def get_headers(self, index, url_refer=None):
        user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
        headers = [
                    {
                        "User-Agent": user_agent,
                        "Accept": "application/json, text/plain, */*",
                        "Content-Type": "application/json;charset=utf-8",
                        "Referer": "https://apps.dos.ny.gov/publicInquiry/"
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

    # output jsonline       
    def jsonl_out(self, items):
        date = self.helpers.date_current()        
        file_name = "{}_{}.jsonl".format(self.STATE, date)
        with jsonlines.open( os.path.join(self.FOLDER, file_name), mode ='a') as writer:
            writer.write(items)   

    def get_params(self, index, search_id, entity_name=None):
        params = [ 
            {
                "searchValue": search_id,
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
                "SearchID": search_id,
            },
            {
                "SearchID": search_id,
                "AssumedNameFlag": "false",
                "ListSortedBy": "ALL",
                "listPaginationInfo": {"listStartRecord": 1, "listEndRecord": 50}
            }
        ]

        return params[index]

    def parser_items_details(self, search_id):
        print(search_id)
        URL_ENTITY_INFORMATION = urljoin(
            self.URL_BASE, "PublicInquiryWeb/api/PublicInquiry/GetEntityRecordByID")
        response = self.pr.set_request(URL_ENTITY_INFORMATION, 
            headers=self.get_headers(1), 
            params=self.get_params(
                1, 
                search_id=search_id)
            )
        if response:
            parsed = response.json()
            items = {"entity_information": parsed}

            URL_ENTITY_ASSUMED_NAME_HISTORY = urljoin(
                self.URL_BASE, "PublicInquiryWeb/api/PublicInquiry/GetAssumedNameHistoryByID")
            response = self.pr.set_request(URL_ENTITY_ASSUMED_NAME_HISTORY, 
            headers=self.get_headers(2), 
            params=self.get_params(2, 
                search_id=search_id))
            if response:
                parsed = response.json()
                items = {**items, **{"entity_assumed_name_history": parsed}}

            return items

    def parser_items(self, id):
        items = self.parser_items_details(id)
        return items

    def run(self):
        for id in range(self.START_ID, self.END_ID):
            id = str(id)
            try:
                items = self.parser_items(id)
                self.jsonl_out(items)
                print(items)
                print("*" *75)                
            except Exception as e:
                print("Oops!!: ", e)


if __name__ == "__main__":
    Scraper().run()