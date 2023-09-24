# -*- coding: utf-8 -*-

import re
import time

from pyload.core.network.http.exceptions import BadHeader

from ..base.account import BaseAccount


class OneFichierCom(BaseAccount):
    __name__ = "OneFichierCom"
    __type__ = "account"
    __version__ = "0.25"
    __status__ = "testing"

    __description__ = """1fichier.com account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("Elrick69", "elrick69[AT]rocketmail[DOT]com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    VALID_UNTIL_PATTERN = r'valid until <span style="font-weight:bold">(\d+\-\d+\-\d+)<'

    def grab_info(self, user, password, data):
        validuntil = None
        trafficleft = -1
        premium = False

        html = self.load("https://1fichier.com/console/abo.pl")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m is not None:
            expire_date = m.group(1)
            self.log_debug("Expire date: " + expire_date)

            try:
                validuntil = time.mktime(time.strptime(expire_date, "%Y-%m-%d"))

            except Exception as exc:
                self.log_error(exc)

            else:
                premium = True

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        login_url = "https://1fichier.com/login.pl?lg=en"

        html = self.load(login_url)
        if "/logout.pl" in html:
            self.skip_login()

        try:
            html = self.load(
                login_url,
                ref=login_url,
                post={
                    "mail": user,
                    "pass": password,
                    "lt": "on",
                    "purge": "off",
                    "valider": "OK",
                },
            )

            if any(
                x in html
                for x in (
                    ">Invalid username or Password",
                    ">Invalid email address",
                    ">Invalid password",
                    ">Invalid username",
                )
            ):
                self.fail_login()

        except BadHeader as exc:
            if exc.code == 403:
                self.fail_login()
            else:
                raise
