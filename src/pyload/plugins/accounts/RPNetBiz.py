# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class RPNetBiz(MultiAccount):
    __name__ = "RPNetBiz"
    __type__ = "account"
    __version__ = "0.22"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """RPNet.biz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Dman", "dmanugm@gmail.com")]

    def grab_hosters(self, user, password, data):
        res = self.load(
            "https://premium.rpnet.biz/client_api.php",
            get={"username": user, "password": password, "action": "showHosterList"},
        )
        hoster_list = json.loads(res)

        #: If account is not valid thera are no hosters available
        if "error" in hoster_list:
            return []

        #: Extract hosters from json file
        return hoster_list["hosters"]

    def grab_info(self, user, password, data):
        #: Get account information from rpnet.biz
        res = self.get_account_status(user, password)
        try:
            if res["accountInfo"]["isPremium"]:
                #: Parse account info. Change the trafficleft later to support per host info.
                account_info = {
                    "validuntil": float(res["accountInfo"]["premiumExpiry"]),
                    "trafficleft": -1,
                    "premium": True,
                }
            else:
                account_info = {
                    "validuntil": None,
                    "trafficleft": None,
                    "premium": False,
                }

        except KeyError:
            #: Handle wrong password exception
            account_info = {"validuntil": None, "trafficleft": None, "premium": False}

        return account_info

    def signin(self, user, password, data):
        #: Get account information from rpnet.biz
        res = self.get_account_status(user, password)

        #: If we have an error in the res, we have wrong login information
        if "error" in res:
            self.fail_login()

    def get_account_status(self, user, password):
        #: Using the rpnet API, check if valid premium account
        res = self.load(
            "https://premium.rpnet.biz/client_api.php",
            get={
                "username": user,
                "password": password,
                "action": "showAccountInformation",
            },
        )
        self.log_debug(f"JSON data: {res}")

        return json.loads(res)
