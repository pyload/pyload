# -*- coding: utf-8 -*-

import json
import time

from ..base.account import BaseAccount


class FilejokerNet(BaseAccount):
    __name__ = "FilejokerNet"
    __type__ = "account"
    __version__ = "0.04"
    __status__ = "testing"

    __description__ = """Filejoker.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://filejoker.net/zapi"

    def api_request(self, op, **kwargs):
        args = {"op": op}
        args.update(kwargs)
        return json.loads(self.load(self.API_URL, get=args))

    def grab_info(self, user, password, data):
        api_data = self.api_request("my_account", session=data["session"])
        premium_expire = api_data.get("usr_premium_expire")

        validuntil = (
            time.mktime(time.strptime(premium_expire, "%Y-%m-%d %H:%M:%S"))
            if premium_expire
            else -1
        )
        trafficleft = (
            int(api_data["traffic_left"]) * 1024 ** 2 if "traffic_left" in api_data else None
        )
        premium = bool(premium_expire)

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        session = data.get("session")
        if session and "error" not in self.api_request("my_account", session=session):
            self.skip_login()

        api_data = self.api_request("login", **{"email": user, "pass": password})
        if "error" in api_data:
            self.fail_login()

        data["session"] = api_data["session"]
