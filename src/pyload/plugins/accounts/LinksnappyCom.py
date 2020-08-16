# -*- coding: utf-8 -*-

import json

from ..base.multi_account import MultiAccount


class LinksnappyCom(MultiAccount):
    __name__ = "LinksnappyCom"
    __type__ = "account"
    __version__ = "0.17"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Linksnappy.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://linksnappy.com/api/"

    def api_response(self, method, **kwargs):
        return json.loads(self.load(self.API_URL + method, get=kwargs))

    def grab_hosters(self, user, password, data):
        json_data = self.api_response("FILEHOSTS")
        return list(json_data["return"].keys())

    def grab_info(self, user, password, data):
        premium = True
        validuntil = None
        trafficleft = None

        json_data = self.api_response("USERDETAILS", username=user, password=password)

        if json_data["status"] != "OK":
            self.log_error(json_data["error"])

        else:
            validuntil = json_data["return"]["expire"]

            if validuntil == "lifetime":
                validuntil = -1

            elif validuntil == "expired":
                premium = False

            else:
                validuntil = float(validuntil)

            if "trafficleft" not in json_data["return"] or isinstance(
                json_data["return"]["trafficleft"], str
            ):
                trafficleft = -1

            else:
                # TODO: Remove `>> 10` in 0.6.x
                trafficleft = float(json_data["return"]["trafficleft"]) >> 10

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        json_data = self.api_response("AUTHENTICATE", username=user, password=password)

        if json_data["status"] != "OK":
            self.fail_login(json_data["error"])
