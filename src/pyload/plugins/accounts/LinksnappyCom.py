# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class LinksnappyCom(MultiAccount):
    __name__ = "LinksnappyCom"
    __type__ = "account"
    __version__ = "0.22"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Linksnappy.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://linksnappy.com/api/"

    def api_request(self, method, **kwargs):
        return json.loads(self.load(self.API_URL + method, get=kwargs))

    def grab_hosters(self, user, password, data):
        json_data = self.api_request("FILEHOSTS")
        return [k for k, v in json_data["return"].items() if v["Status"] == "1"]

    def grab_info(self, user, password, data):
        premium = True
        validuntil = None
        trafficleft = None

        json_data = self.api_request("USERDETAILS", username=user, password=password)

        if json_data["status"] != "OK":
            self.log_error(json_data["error"])

        else:
            expire = json_data["return"]["expire"]

            if expire == "lifetime":
                validuntil = -1

            elif expire == "expired":
                premium = False

            else:
                validuntil = float(expire)

            if isinstance(json_data["return"].get("trafficleft", ""), str):
                trafficleft = -1

            else:
                trafficleft = float(json_data["return"]["trafficleft"]) * 1024

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        json_data = self.api_request("AUTHENTICATE", username=user, password=password)

        if json_data["status"] != "OK":
            self.fail_login(json_data["error"])
