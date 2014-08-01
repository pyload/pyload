# -*- coding: utf-8 -*-

import re
from time import time

from module.plugins.Account import Account


class UploadedTo(Account):
    __name__ = "UploadedTo"
    __type__ = "account"
    __version__ = "0.26"

    __description__ = """Uploaded.to account plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"


    def loadAccountInfo(self, user, req):

        req.load("http://uploaded.net/language/en")
        html = req.load("http://uploaded.net/me")

        premium = '<a href="register"><em>Premium</em>' in html or '<em>Premium</em></th>' in html

        if premium:
            raw_traffic = re.search(r'<th colspan="2"><b class="cB">([^<]+)', html).group(1).replace('.', '')
            raw_valid = re.search(r"<td>Duration:</td>\s*<th>([^<]+)", html, re.MULTILINE).group(1).strip()

            traffic = int(self.parseTraffic(raw_traffic))

            if raw_valid == "unlimited":
                validuntil = -1
            else:
                raw_valid = re.findall(r"(\d+) (Week|weeks|days|day|hours|hour)", raw_valid)
                validuntil = time()
                for n, u in raw_valid:
                    validuntil += int(n) * 60 * 60 * {"Week": 168, "weeks": 168, "days": 24,
                                                      "day": 24, "hours": 1, "hour": 1}[u]

            return {"validuntil": validuntil, "trafficleft": traffic, "maxtraffic": 50 * 1024 * 1024}
        else:
            return {"premium": False, "validuntil": -1}

    def login(self, user, data, req):

        req.load("http://uploaded.net/language/en")
        req.cj.setCookie("uploaded.net", "lang", "en")

        page = req.load("http://uploaded.net/io/login", post={"id": user, "pw": data['password'], "_": ""})

        if "User and password do not match!" in page:
            self.wrongPassword()
