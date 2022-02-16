# -*- coding: utf-8 -*-

import json

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_account import MultiAccount


class MultishareCz(MultiAccount):
    __name__ = "MultishareCz"
    __type__ = "account"
    __version__ = "0.15"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Multishare.cz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    #: See https://multishare.cz/api/
    API_URL = "https://www.multishare.cz/api/"

    def api_request(self, method, **kwargs):
        get = {"sub": method}
        get.update(kwargs)
        self.req.http.c.setopt(pycurl.USERAGENT, "JDownloader")
        json_data = self.load(self.API_URL, get=get)

        if not json_data.startswith("{"):
            if json_data.startswith("ERR:"):
                json_data = json_data[4:].strip()
            return {"err": json_data}

        else:
            return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        api_data = self.api_request("supported-hosters")
        return api_data["server"]

    def grab_info(self, user, password, data):
        api_data = self.api_request("account-details", login=user, password=password)
        trafficleft = self.parse_traffic(api_data["credit"], "MB")

        premium = True if trafficleft else False

        return {"validuntil": -1, "trafficleft": trafficleft, "premium": premium}

    def signin(self, user, password, data):
        try:
            api_data = self.api_request(
                "account-details", login=user, password=password
            )

        except BadHeader as exc:
            if exc.code == 403:
                self.fail_login(_("IP is banned"))
            else:
                raise

        if "err" in api_data:
            self.fail_login(api_data["err"])
