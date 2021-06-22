# -*- coding: utf-8 -*-

import json
import time
from hashlib import sha256

import pycurl

from ..base.multi_account import MultiAccount


class GetTwentyFourOrg(MultiAccount):
    __name__ = "GetTwentyFourOrg"
    __type__ = "account"
    __version__ = "0.04"
    __status__ = "testing"

    __description__ = "GeT24.org account plugin"
    __license__ = "GPLv3"
    __authors__ = ["get24", "contact@get24.org"]

    API_URL = "https://get24.org/api/"

    def api_request(self, method, **kwargs):
        self.req.http.c.setopt(
            pycurl.USERAGENT, "pyLoad/{}".format(self.pyload.version).encode()
        )
        json_data = self.load(self.API_URL + method, post=kwargs)
        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        hosts = self.api_request("hosts/enabled")
        self.log_debug(hosts)
        return hosts

    def grab_info(self, user, password, data):
        rc = self.api_request(
            "login", email=user, passwd_sha256=self.info["data"]["passwd_sha256"]
        )
        self.log_debug(rc)

        validuntil = time.mktime(time.strptime(rc["date_expire"], "%Y-%m-%d %H:%M:%S"))

        return {
            "validuntil": validuntil,
            "trafficleft": rc["transfer_left"] * 2 ** 30,  # gb -> b
            "premium": rc["status"] == "premium",
        }

    def signin(self, user, password, data):
        data["passwd_sha256"] = sha256(password.encode("ascii")).hexdigest()
        rc = self.api_request("login", email=user, passwd_sha256=data["passwd_sha256"])
        if rc.get("ok") is False:
            self.log_error(rc["reason"])
            self.fail_login()
