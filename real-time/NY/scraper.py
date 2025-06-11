#!/usr/bin/env python
# coding: utf8

from urllib.parse import urljoin

from process_request import ProcessRequest 


class Scraper:
    def __init__(self, id):
        self.id = id
        self.pr = ProcessRequest()
        
        self.URL_BASE = "https://apps.dos.ny.gov"

        self.STATE = "new_york"

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

    def parser_items_details(self):
        items = {}
        URL_ENTITY_INFORMATION = urljoin(
            self.URL_BASE, "PublicInquiryWeb/api/PublicInquiry/GetEntityRecordByID")
        response = self.pr.set_request(URL_ENTITY_INFORMATION, 
            headers=self.get_headers(1), 
            params=self.get_params(1)
        )
        if response:
            parsed = response.json()
            items = {"entity_information": parsed}

            URL_ENTITY_ASSUMED_NAME_HISTORY = urljoin(
                self.URL_BASE, "PublicInquiryWeb/api/PublicInquiry/GetAssumedNameHistoryByID")
            response = self.pr.set_request(URL_ENTITY_ASSUMED_NAME_HISTORY, 
            headers=self.get_headers(2), 
            params=self.get_params(2))
            if response:
                parsed = response.json()
                items = {**items, **{"entity_assumed_name_history": parsed}}

        return items

    def parser_items(self):
        items = self.parser_items_details()
        return items

    def parser(self):        
        if self.id:
            try:
                items = self.parser_items() 
            except Exception as e:
                print(e, "@@@")
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
                "message": "Input parameters failure...!!!"
            }                    

        return result