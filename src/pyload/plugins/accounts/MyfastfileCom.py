# -*- coding: utf-8 -*-
import json
import time
from datetime import timedelta

from ..base.multi_account import MultiAccount


class MyfastfileCom(MultiAccount):
    __name__ = "MyfastfileCom"
    __type__ = "account"
    __version__ = "0.12"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Myfastfile.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("stickell", "l.stickell@yahoo.it")]

    def grab_hosters(self, user, password, data):
        json_data = self.load("http://myfastfile.com/api.php", get={"hosts": ""})
        self.log_debug("JSON data", json_data)
        json_data = json.loads(json_data)

        return json_data["hosts"]

    def grab_info(self, user, password, data):
        if "days_left" in self.json_data:
            validuntil = (
                time.time() + timedelta(hours=self.json_data["days_left"] * 24).seconds
            )
            return {"premium": True, "validuntil": validuntil, "trafficleft": -1}
        else:
            self.log_error(self._("Unable to get account information"))

    def signin(self, user, password, data):
        #: Password to use is the API-Password written in http://myfastfile.com/myaccount
        html = self.load(
            "https://myfastfile.com/api.php", get={"user": user, "pass": password}
        )

        self.log_debug("JSON data: " + html)

        self.json_data = json.loads(html)
        if self.json_data["status"] != "ok":
            self.fail_login(self._("Invalid username or password"))
