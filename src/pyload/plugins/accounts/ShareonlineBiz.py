# -*- coding: utf-8 -*-

from ..base.account import BaseAccount
from ..helpers import set_cookie


class ShareonlineBiz(BaseAccount):
    __name__ = "ShareonlineBiz"
    __type__ = "account"
    __version__ = "0.46"
    __status__ = "testing"

    __description__ = """Share-online.biz account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    def api_response(self, user, password):
        res = self.load(
            "https://api.share-online.biz/cgi-bin",
            get={
                "q": "userdetails",
                "aux": "traffic",
                "username": user,
                "password": password,
            },
            decode=False,
        )

        api = dict(line.split("=") for line in res.splitlines() if "=" in line)

        if "a" not in api:
            self.fail_login(res.strip("*"))

        return api

    def grab_info(self, user, password, data):
        premium = False
        validuntil = None
        trafficleft = -1
        maxtraffic = 100 << 30  #: 100 GiB

        api_info = self.api_response(user, password)

        premium = api_info["group"] in (
            "PrePaid",
            "Premium",
            "Penalty-Premium",
            "VIP",
            "VIP-Special",
        )
        validuntil = float(api_info["expire_date"])
        traffic = float(api_info["traffic_1d"].split(";")[0])

        if maxtraffic > traffic:
            trafficleft = maxtraffic - traffic
        else:
            trafficleft = -1

        maxtraffic >>= 10  # TODO: Remove `>> 10` in 0.6.x
        trafficleft >>= 10  # TODO: Remove `>> 10` in 0.6.x

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "maxtraffic": maxtraffic,
        }

    def signin(self, user, password, data):
        api_info = self.api_response(user, password)
        set_cookie(self.req.cj, "share-online.biz", "a", api_info["a"])
