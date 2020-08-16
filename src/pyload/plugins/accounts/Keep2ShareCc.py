# -*- coding: utf-8 -*-

import json

from pyload.core.network.http.exceptions import BadHeader
from pyload.core.network.request_factory import get_url

from ..base.account import BaseAccount


class Keep2ShareCc(BaseAccount):
    __name__ = "Keep2ShareCc"
    __type__ = "account"
    __version__ = "0.15"
    __status__ = "testing"

    __description__ = """Keep2Share.cc account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("aeronaut", "aeronaut@pianoguy.de"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://keep2share.cc/api/v2/"
    #: See https://github.com/keep2share/api

    @classmethod
    def api_response(cls, method, **kwargs):
        html = get_url(cls.API_URL + method, post=json.dumps(kwargs))
        return json.loads(html)

    def grab_info(self, user, password, data):
        json_data = self.api_response("AccountInfo", auth_token=data["token"])

        return {
            "validuntil": json_data["account_expires"],
            # TODO: Remove `>> 10` in 0.6.x
            "trafficleft": json_data["available_traffic"] >> 10,
            "premium": True,
        }

    def signin(self, user, password, data):
        if "token" in data:
            try:
                json_data = self.api_response("test", auth_token=data["token"])

            except BadHeader as exc:
                if exc.code == 403:
                    pass

                else:
                    raise
            else:
                self.skip_login()

        try:
            json_data = self.api_response("login", username=user, password=password)

        except BadHeader as exc:
            if exc.code == 406:
                self.fail_login()

            else:
                raise

        else:
            data["token"] = json_data["auth_token"]
