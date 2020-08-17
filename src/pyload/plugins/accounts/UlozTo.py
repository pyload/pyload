# -*- coding: utf-8 -*-

import json
import re
import time
import urllib.parse

import pycurl

from ..base.account import BaseAccount
from ..helpers import parse_html_form, timestamp


class UlozTo(BaseAccount):
    __name__ = "UlozTo"
    __type__ = "account"
    __version__ = "0.33"
    __status__ = "testing"

    __description__ = """Uloz.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("zoidberg", "zoidberg@mujmail.cz"),
        ("pulpe", None),
        ("ondrej", "git@ondrej.it"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    INFO_PATTERN = r'title="credit in use"><\/span>\s*([\d.,]+) ([\w^_]+)\s*<\/td>\s*<td class="right">([\d.]+)<\/td>'

    def grab_info(self, user, password, data):
        self.req.http.c.setopt(pycurl.HTTPHEADER, ["X-Requested-With: XMLHttpRequest"])
        try:
            html = json.loads(
                self.load(
                    "https://ulozto.net/statistiky",
                    get={"do": "overviewPaymentsView-ajaxLoad", "_": timestamp()},
                )
            )["snippets"]["snippet-overviewPaymentsView-"]

        except (ValueError, KeyError):
            self.log_error(
                self._("Unable to retrieve account information, unexpected response")
            )
            return {"validuntil": None, "trafficleft": None, "premium": False}

        if ">You don't have any credit at the moment.<" in html:  #: Free account
            validuntil = -1
            trafficleft = -1
            premium = False

        else:
            m = re.search(self.INFO_PATTERN, html)
            if m is not None:
                validuntil = time.mktime(
                    time.strptime(m.group(3) + " 23:59:59", "%d.%m.%Y %H:%M:%S")
                )
                trafficleft = self.parse_traffic(m.group(1), m.group(2))
                premium = True if trafficleft else False

            else:
                self.log_error(
                    self._("Unable to retrieve account information, pattern not found")
                )
                validuntil = None
                trafficleft = None
                premium = False

        return {
            "validuntil": validuntil,
            "trafficleft": trafficleft,
            "premium": premium,
        }

    def signin(self, user, password, data):
        html = self.load("https://ulozto.net/?do=web-login")
        if ">Log out<" in html:
            self.skip_login()

        url, inputs = parse_html_form('action="/login"', html)
        if inputs is None:
            self.fail_login("Login form not found")

        inputs["username"] = user
        inputs["password"] = password

        html = self.load(urllib.parse.urljoin("https://ulozto.net/", url), post=inputs)
        if not ">Log out<" in html:
            self.fail_login()
