# -*- coding: utf-8 -*-

import re
from time import time

from module.plugins.Account import Account


class UploadedTo(Account):
    __name__    = "UploadedTo"
    __type__    = "account"
    __version__ = "0.30"

    __description__ = """Uploaded.to account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    PREMIUM_PATTERN = r'<em>Premium</em>'
    VALID_UNTIL_PATTERN = r'<td>Duration:</td>\s*<th>(.+?)<'
    TRAFFIC_LEFT_PATTERN = r'<b class="cB">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = None

        html = req.load("http://uploaded.net/me")

        premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html, re.M)
        if m:
            expiredate = m.group(1).lower().strip()

            if expiredate == "unlimited":
                validuntil = -1
            else:
                m = re.findall(r'(\d+) (week|day|hour)', expiredate)
                if m:
                    validuntil = time()
                    for n, u in m:
                        validuntil += float(n) * 60 * 60 * {'week': 168, 'day': 24, 'hour': 1}[u]

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            traffic = m.groupdict()
            size    = traffic['S'].replace('.', '')
            unit    = traffic['U'].lower()

            if unit.startswith('t'):  #@NOTE: Remove in 0.4.10
                trafficleft = float(size.replace(',', '.')) / 1024
                trafficleft *= 1 << 40
            else:
                trafficleft = self.parseTraffic(size + unit)

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}


    def login(self, user, data, req):
        # req.cj.setCookie("uploaded.net", "lang", "en")

        html = req.load("http://uploaded.net/io/login",
                        post={'id': user, 'pw': data['password'], '_': ""},
                        decode=True)

        if '"err"' in html:
            self.wrongPassword()
