# -*- coding: utf-8 -*-
import json
import time

from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class TenluaVn(BaseAccount):
    __name__ = "TenluaVn"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __description__ = """TenluaVn account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    API_URL = "https://api2.tenlua.vn/"

    def api_request(self, method, **kwargs):
        kwargs["a"] = method
        sid = kwargs.pop("sid", None)
        return json.loads(
            self.load(
                self.API_URL,
                get={"sid": sid} if sid is not None else {},
                post=json.dumps([kwargs]),
            )
        )

    def grab_info(self, user, password, data):
        user_info = self.api_request("user_info", sid=data["sid"])[0]

        validuntil = time.mktime(time.strptime(user_info["endGold"], "%d-%m-%Y"))
        premium = user_info["free_used"] != "null"

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def signin(self, user, password, data):
        try:
            login_info = self.api_request(
                "user_login", user=user, password=password, permanent=False
            )

        except BadHeader as exc:
            if exc.code == 401:
                self.fail_login()

            else:
                self.fail_login(self._("BadHeader {}").format(exc.code))

        data["sid"] = login_info[0]
