# -*- coding: utf-8 -*-

import time

from ..base.multi_account import MultiAccount


class SimplydebridCom(MultiAccount):
    __name__ = "SimplydebridCom"
    __type__ = "account"
    __version__ = "0.20"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter hosters to use", "all"),
        ("mh_list", "str", "Hoster list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = """Simply-Debrid.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Kagenoshin", "kagenoshin@gmx.ch"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    def grab_hosters(self, user, password, data):
        html = self.load("http://simply-debrid.com/api.php", get={"list": 1})
        return [x for x in html.split(";") if x]

    def grab_info(self, user, password, data):
        res = self.load(
            "http://simply-debrid.com/api.php",
            get={"login": 2, "u": user, "p": password},
        )
        data = [x.strip() for x in res.split(";")]
        if str(data[0]) != "1":
            return {"premium": False}
        else:
            return {
                "premium": True,
                "trafficleft": -1,
                "validuntil": time.mktime(time.strptime(str(data[2]), "%d/%m/%Y")),
            }

    def signin(self, user, password, data):
        res = self.load(
            "https://simply-debrid.com/api.php",
            get={"login": 1, "u": user, "p": password},
        )
        if res != "02: loggin success":
            self.fail_login()
