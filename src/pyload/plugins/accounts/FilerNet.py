import json
import time

from ..base.account import BaseAccount


class FilerNet(BaseAccount):
    __name__ = "FilerNet"
    __type__ = "account"
    __version__ = "0.18"
    __status__ = "testing"

    __description__ = """Filer.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    # See https://filer.net/api
    API_URL = "https://filer.net/api/"

    def grab_info(self, user, password, data):
        self.req.add_auth(f"{user}:{password}")
        try:
            json_data = self.load(self.API_URL + "profile.json")
            api_data = json.loads(json_data)["data"]
        except Exception as e:
            self.log_error(str(e))
            return {"premium": False, "validuntil": None, "trafficleft": None}
        finally:
            self.req.remove_auth()

        premium = api_data["premium"]

        #: Free user
        if premium is False:
            return {"premium": False, "validuntil": None, "trafficleft": None}

        validuntil = api_data["until"]
        trafficleft = api_data["traffic_left"]

        return {"premium": premium, "validuntil": validuntil, "trafficleft": trafficleft}

    def signin(self, user, password, data):
        self.req.add_auth(f"{user}:{password}")
        try:
            self.load(self.API_URL + "profile.json")
        except Exception as e:
            self.fail_login(str(e))
        else:
            self.skip_login()
        finally:
            self.req.remove_auth()
