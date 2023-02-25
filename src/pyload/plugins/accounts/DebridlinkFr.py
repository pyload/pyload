# -*- coding: utf-8 -*-

import json
import time

import pycurl
from pyload.core.network.http.exceptions import BadHeader

from ..base.multi_account import MultiAccount
from ..downloaders.DebridlinkFr import error_description


class DebridlinkFr(MultiAccount):
    __name__ = "DebridlinkFr"
    __type__ = "account"
    __version__ = "0.06"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Debridlink.fr account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    TUNE_TIMEOUT = False

    #: See https://debrid-link.fr/api_doc/v2
    API_URL = "https://debrid-link.fr/api/"

    def api_request(self, method, get={}, post={}):
        api_token = self.info["data"].get("api_token", None)
        if api_token and method != "oauth/token":
            self.req.http.c.setopt(
                pycurl.HTTPHEADER, ["Authorization: Bearer " + api_token]
            )
        self.req.http.c.setopt(pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version))
        try:
            json_data = self.load(self.API_URL + method, get=get, post=post)
        except BadHeader as exc:
            json_data = exc.content

        return json.loads(json_data)

    def _refresh_token(self, client_id, refresh_token):
        api_data = self.api_request(
            "oauth/token",
            post={
                "client_id": client_id,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )

        if "error" in api_data:
            if api_data["error"] == "invalid_request":
                self.log_error(
                    self._(
                        "You have to use GetDebridlinkToken.py to authorize pyLoad: "
                        "https://github.com/pyload/pyload/files/9353788/GetDebridlinkToken.zip"
                    )
                )
            else:
                self.log_error(
                    api_data.get(
                        "error_description", error_description(api_data["error"])
                    )
                )
            self.fail_login()

        return api_data["access_token"], api_data["expires_in"]

    def grab_hosters(self, user, password, data):
        api_data = self.api_request("v2/downloader/hostnames")

        if api_data["success"]:
            return api_data["value"]

        else:
            return []

    def grab_info(self, user, password, data):
        api_data = self.api_request("v2/account/infos")

        if api_data["success"]:
            premium = api_data["value"]["premiumLeft"] > 0
            validuntil = api_data["value"]["premiumLeft"] + time.time()

        else:
            self.log_error(
                self._("Unable to retrieve account information"),
                api_data.get("error_description", error_description(api_data["error"])),
            )
            validuntil = None
            premium = None

        return {"validuntil": validuntil, "trafficleft": -1, "premium": premium}

    def signin(self, user, password, data):
        if "token" not in data:
            api_token, timeout = self._refresh_token(user, password)
            data["api_token"] = api_token
            self.timeout = timeout - 5 * 60  #: Five minutes less to be on the safe side

        api_data = self.api_request("v2/account/infos")
        if "error" in api_data:
            if api_data["error"] == "badToken":  #: Token expired? try to refresh
                api_token, timeout = self._refresh_token(user, password)
                data["api_token"] = api_token
                self.timeout = (
                    timeout - 5 * 60
                )  #: Five minutes less to be on the safe side

            else:
                self.log_error(
                    api_data.get(
                        "error_description", error_description(api_data["error"])
                    )
                )
                self.fail_login()
