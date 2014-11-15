# -*- coding: utf-8 -*-

import re
from time import time

from pyload.plugins.internal.Account import Account


class UploadedTo(Account):
    __name__    = "UploadedTo"
    __type__    = "account"
    __version__ = "0.27"

    __description__ = """Uploaded.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    PREMIUM_PATTERN = r'<em>Premium</em>'
    VALID_UNTIL_PATTERN = r'<td>Duration:</td>\s*<th>([^<]+)'
    TRAFFIC_LEFT_PATTERN = r'<th colspan="2"><b class="cB">([^<]+)'


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = None

        html = req.load("http://uploaded.net/me")

        premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html, re.M)
        if m:
            expiredate = m.group(1).strip()

            if expiredate == "unlimited":
                validuntil = -1
            else:
                m = re.findall(r'(\d+) (Week|weeks|day|hour)', expiredate)
                if m:
                    validuntil = time()
                    for n, u in m:
                        validuntil += int(n) * 60 * 60 * {'Week': 168, 'weeks': 168, 'day': 24, 'hour': 1}[u]

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = self.parseTraffic(m.group(1).replace('.', ''))

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, data, req):
        req.cj.setCookie(".uploaded.net", "lang", "en")

        page = req.load("http://uploaded.net/io/login",
                        post={'id': user, 'pw': data['password'], '_': ""})

        if "User and password do not match" in page:
            self.wrongPassword()
