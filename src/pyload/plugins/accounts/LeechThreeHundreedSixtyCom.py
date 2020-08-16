# -*- coding: utf-8 -*-

import json
import time
from datetime import timedelta

from ..base.multi_account import MultiAccount


class LeechThreeHundreedSixtyCom(MultiAccount):
    __name__ = "LeechThreeHundreedSixtyCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Leech360.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    LOGIN_TIMEOUT = timedelta(minutes=8).seconds
    TUNE_TIMEOUT = False

    API_URL = "https://leech360.com/api/get_"

    def api_response(self, method, **kwargs):
        if "pass_" in kwargs:
            kwargs["pass"] = kwargs.pop("pass_")
        json_data = self.load(self.API_URL + method, get=kwargs)
        return json.loads(json_data)

    def grab_hosters(self, user, password, data):
        api_data = self.api_response("support", token=data["token"])
        valid_status = ("online", "vip") if self.info["data"]["premium"] else ("online")
        return [
            h["hostname"]
            for h in api_data["data"].values()
            if h["status"] in valid_status
        ]

    def grab_info(self, user, password, data):
        api_data = self.api_response("userinfo", token=data["token"])

        premium_expire = int(api_data["data"].get("premium_expire", 0))
        status = api_data["data"]["status"]

        if status == "lifetime":
            premium = True
            validuntil = -1

        elif premium_expire > 0:
            premium = True
            validuntil = float(premium_expire)

        else:
            premium = False
            validuntil = time.mktime(time.strptime(status, "%b d %Y %I:%M %p"))

        # TODO: Remove `>> 10` in 0.6.x
        trafficleft = (
            536_870_912_000 - int(api_data["data"].get("total_used", 0))
        ) >> 10
        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
        }

    def signin(self, user, password, data):
        api_data = self.api_response("token", user=user, pass_=password)
        if api_data["error"]:
            self.log_warning(api_data["error_message"])
            self.fail_login()

        data["token"] = api_data["token"]
