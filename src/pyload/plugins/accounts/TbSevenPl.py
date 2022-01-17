# -*- coding: utf-8 -*-

import re
import time

from ..base.multi_account import MultiAccount


class TbSevenPl(MultiAccount):
    __name__ = "TbSevenPl"
    __type__ = "account"
    __version__ = "0.02"
    __status__ = "testing"

    __config__ = [
        ("mh_mode", "all;listed;unlisted", "Filter downloaders to use", "all"),
        ("mh_list", "str", "Downloader list (comma separated)", ""),
        ("mh_interval", "int", "Reload interval in hours", 12),
    ]

    __description__ = "tb7.pl account plugin"
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    VALID_UNTIL_PATTERN = r"Dostęp Premium ważny do <b>([\d. /:]+?)<"
    TRAFFIC_LEFT_PATTERN = (
        r"Pozostały Limit Premium do wykorzystania: <b>(?P<S>[\d.,]+) (?P<U>[\w^_]+)"
    )

    def grab_hosters(self, user, password, data):
        hosts = self.load("https://tb7.pl/jdhostingi.txt")
        return hosts.splitlines()

    def grab_info(self, user, password, data):
        premium = True
        validuntil = None
        trafficleft = None

        html = self.load("https://tb7.pl/")
        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            validuntil = time.mktime(time.strptime(m.group(1), "%d.%m.%Y / %H:%M"))

        else:
            self.log_error("VALID_UNTIL_PATTERN not found")

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m is not None:
            trafficleft = self.parse_traffic(m.group("S"), m.group("U"))

        else:
            self.log_error("TRAFFIC_LEFT_PATTERN not found")

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        html = self.load("https://tb7.pl/")
        if "Wyloguj" in html:
            self.skip_login()

        html = self.load(
            "https://tb7.pl/login", post={"login": user, "password": password}
        )
        if "Wyloguj" not in html:
            self.fail_login()
