# -*- coding: utf-8 -*-
import json
import time

from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_account import MultiAccount


def args(**kwargs):
    return kwargs


class RealdebridCom(MultiAccount):
    __name__ = "RealdebridCom"
    __type__ = "account"
    __version__ = "0.58"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Real-Debrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Devirex Hazzard", "naibaf_11@yahoo.de"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://api.real-debrid.com/rest/1.0"

    def api_response(self, namespace, get={}, post={}):
        json_data = self.load(self.API_URL + namespace, get=get, post=post)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        hosters = self.api_response("/hosts/domains")
        return hosters

    def grab_info(self, user, password, data):
        account = self.api_response("/user", args(auth_token=password))

        validuntil = time.time() + account["premium"]

        return {"validuntil": validuntil, "trafficleft": -1, "premium": True}

    def signin(self, user, password, data):
        try:
            account = self.api_response("/user", args(auth_token=password))

        except BadHeader as exc:
            if exc.code == 401:
                self.log_error(
                    self._(
                        "Password for Real-debrid should be the API token - get it from: https://real-debrid.com/apitoken"
                    )
                )
                self.fail_login()

            else:
                raise

        if user != account["username"]:
            self.fail_login()
