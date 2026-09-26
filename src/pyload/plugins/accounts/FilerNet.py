import json
from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class FilerNet(BaseAccount):
    __name__ = "FilerNet"
    __type__ = "account"
    __version__ = "0.20"
    __status__ = "testing"

    __description__ = """Filer.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://filer.net/api
    API_URL = "https://filer.net/api/"

    def api_request(self, method, user=None, password=None):
        try:
            if user and password:
                self.req.add_auth(f"{user}:{password}")
            json_data = self.load(f"{self.API_URL}{method}.json", redirect=False)
        except BadHeader as exc:
            json_data = exc.content
        finally:
            if user and password:
                self.req.remove_auth()

        return json.loads(json_data)

    def grab_info(self, user, password, data):
        api_data = self.api_request("profile", user, password)
        user_data = api_data.get("data", {})
        premium = user_data.get("premium", False)
        if premium:
            until = user_data.get("until")
            validuntil = until if until and until is not False else None
            trafficleft = user_data.get("traffic_left", 0)
        else:
            validuntil = None
            trafficleft = 0

        return {
            "premium": premium,
            "validuntil": validuntil,
            "trafficleft": trafficleft
        }

    def signin(self, user, password, data):
        api_data = self.api_request("profile", user, password)
        if api_data.get("code") != 200:
            self.fail_login(api_data.get("status", "unknown"))
