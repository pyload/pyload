# -*- coding: utf-8 -*-

import json
import pycurl

from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class PixeldrainCom(BaseAccount):
    __name__ = "PixeldrainCom"
    __type__ = "account"
    __version__ = "0.01"
    __status__ = "testing"

    __description__ = """Pixeldrain.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    #: See https://pixeldrain.com/api/
    API_URL = "https://pixeldrain.com/api/"

    def grab_info(self, user, password, data):
        # unfortunately, there is no method for account info, assume premium
        return {
            "validuntil": -1,
            "trafficleft": -1,
            "premium": True
        }

    def signin(self, user, password, data):
        self.req.http.c.setopt(pycurl.USERPWD, f":{password}")
        try:
            json_data = self.load(f"{self.API_URL}/user/lists")
        except BadHeader as exc:
            json_data = exc.content

        api_data = json.loads(json_data)
        if not api_data.get("success", True):
            self.log_error(api_data["message"])
            self.fail_login()
