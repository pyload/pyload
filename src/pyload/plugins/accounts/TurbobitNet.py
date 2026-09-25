import json
import time

from ..base.account import BaseAccount


class TurbobitNet(BaseAccount):
    __name__ = "TurbobitNet"
    __type__ = "account"
    __version__ = "0.16"
    __status__ = "testing"

    __description__ = """TurbobitNet account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    API_URL = "https://app.turbobit.net/api/"

    def api_request(self, method, **kwargs):
        if kwargs:
            self.req.http.set_header("Content-Type", "application/json")
            post_data = json.dumps(kwargs)
        else:
            post_data = None

        data = self.load(self.API_URL + method, post=post_data)
        return json.loads(data)

    def grab_info(self, user, password, data):
        api_data = self.api_request("user/info")

        if "premium" in api_data and api_data["premium"] .get("status") == "active":
            premium = True
            validuntil = time.mktime(time.strptime(api_data["premium"]["expiredAt"], "%Y-%m-%d %H:%M:%S"))
        else:
            premium = False
            validuntil = -1

        return {"premium": premium, "trafficleft": -1, "validuntil": validuntil}

    def signin(self, user, password, data):
        api_data = self.api_request("auth/login", email=user, password=password)
        if api_data:
            self.fail_login(api_data.get("error_name", "Login handshake has failed"))
