# -*- coding: utf-8 -*-

import hashlib
import json
import time

import pycurl

from ..base.multi_account import MultiAccount


def args(**kwargs):
    return kwargs


class DebridlinkFr(MultiAccount):
    __name__ = "DebridlinkFr"
    __type__ = "account"
    __version__ = "0.03"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Debridlink.fr account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://debrid-link.fr/api"

    def api_request(self, method, data=None, get={}, post={}):

        session = self.info["data"].get("session", None)
        if session:
            ts = str(int(time.time() - float(session["tsd"])))

            m = hashlib.sha1()
            data = ts + method + session["key"]
            m.update(data.encode())
            sign = m.hexdigest()

            self.req.http.c.setopt(
                pycurl.HTTPHEADER,
                [
                    "X-DL-TOKEN: " + session["token"],
                    "X-DL-SIGN: " + sign,
                    "X-DL-TS: " + ts,
                ],
            )

        json_data = self.load(self.API_URL + method, get=get, post=post)

        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        res = self.api_request("/downloader/hostnames")

        if res["result"] == "OK":
            return res["value"]

        else:
            return []

    def grab_info(self, user, password, data):
        res = self.api_request("/account/infos")

        if res["result"] == "OK":
            premium = res["value"]["premiumLeft"] > 0
            validuntil = res["value"]["premiumLeft"] + time.time()

        else:
            self.log_error(self._("Unable to retrieve account information"), res["ERR"])
            validuntil = None
            premium = None

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        cache_info = self.db.retrieve("cache_info", {})
        if user in cache_info:
            self.info["data"]["session"] = cache_info[user]

            res = self.api_request("/account/infos")
            if res["result"] == "OK":
                self.skip_login()

            else:
                del cache_info[user]
                self.db.store("cache_info", cache_info)

        res = self.api_request(
            "/account/login", post=args(pseudo=user, password=password)
        )

        if res["result"] != "OK":
            self.fail_login()

        cache_info[user] = {
            "tsd": time.time() - float(res["ts"]),
            "token": res["value"]["token"],
            "key": res["value"]["key"],
        }

        self.info["data"]["session"] = cache_info[user]
        self.db.store("cache_info", cache_info)
