# -*- coding: utf-8 -*-
import re
import time

from ..base.account import BaseAccount


class FilerNet(BaseAccount):
    __name__ = "FilerNet"
    __type__ = "account"
    __version__ = "0.15"
    __status__ = "testing"

    __description__ = """Filer.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("stickell", "l.stickell@yahoo.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    LOGIN_SKIP_PATTERN = r'<a href="/logout"'
    TOKEN_PATTERN = r'name="_csrf_token" value="(.+?)"'
    VALID_UNTIL_PATTERN = r"Der Premium-Zugang ist gültig bis (.+)\.\s*</td>"
    TRAFFIC_LEFT_PATTERN = r"Traffic</th>\s*<td>([\d.,]+) (?:([\w^_]+))</td>"
    FREE_PATTERN = r"Account Status</th>\s*<td>\s*Free"

    def grab_info(self, user, password, data):
        html = self.load("https://filer.net/profile")

        #: Free user
        if re.search(self.FREE_PATTERN, html) is not None:
            return {"premium": False, "validuntil": None, "trafficleft": None}

        until = re.search(self.VALID_UNTIL_PATTERN, html)
        traffic = re.search(self.TRAFFIC_LEFT_PATTERN, html)

        if until and traffic:
            validuntil = time.mktime(
                time.strptime(until.group(1), "%d.%m.%Y, %H:%M:%S")
            )
            trafficleft = self.parse_traffic(traffic.group(1), traffic.group(2))
            return {
                "premium": True,
                "validuntil": validuntil,
                "trafficleft": trafficleft,
            }

        else:
            self.log_error(self._("Unable to retrieve account information"))
            return {"premium": False, "validuntil": None, "trafficleft": None}

    def signin(self, user, password, data):
        html = self.load("https://filer.net/login")

        if re.search(self.LOGIN_SKIP_PATTERN, html) is not None:
            self.skip_login()

        token = re.search(self.TOKEN_PATTERN, html).group(1)

        html = self.load(
            "https://filer.net/login_check",
            post={
                "_username": user,
                "_password": password,
                "_remember_me": "on",
                "_csrf_token": token,
                "_target_path": "https://filer.net/",
            },
        )

        if re.search(self.LOGIN_SKIP_PATTERN, html) is None:
            self.fail_login()
