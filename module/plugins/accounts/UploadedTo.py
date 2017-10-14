# -*- coding: utf-8 -*-

import re
import time

from ..internal.Account import Account


class UploadedTo(Account):
    __name__ = "UploadedTo"
    __type__ = "account"
    __version__ = "0.46"
    __status__ = "testing"

    __description__ = """Uploaded.to account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    COOKIES = False

    PREMIUM_PATTERN = r'<em>Premium</em>'
    VALID_UNTIL_PATTERN = r'<td>Duration:</td>\s*<th>\s*(.+?)<'
    TRAFFIC_LEFT_PATTERN = r'<b class="cB">(?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    def grab_info(self, user, password, data):
        html = self.load("http://uploaded.net/me")

        premium = True if re.search(self.PREMIUM_PATTERN, html) else False
        if premium:
            validuntil = None
            trafficleft = None

            m = re.search(self.VALID_UNTIL_PATTERN, html, re.M)
            if m is not None:
                expiredate = m.group(1).lower().strip()

                if expiredate == "unlimited":
                    validuntil = -1
                else:
                    m = re.findall(
                        r'(\d+) (week|day|hour|minute|second)', expiredate)
                    if m is not None:
                        validuntil = time.time()
                        for n, u in m:
                            validuntil += float(n) * {
                                'week': 3600 * 168,
                                'day': 3600 * 24,
                                'hour': 3600,
                                'minute': 60,
                                'second': 1}[u]

            m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
            if m is not None:
                traffic = m.groupdict()
                size = traffic['S'].replace('.', '')
                unit = traffic['U'].lower()
                trafficleft = self.parse_traffic(size, unit)

        else:
            validuntil = -1
            trafficleft = -1

        return {'validuntil': validuntil,
                'trafficleft': trafficleft,
                'premium': premium}

    def signin(self, user, password, data):
        try:
            self.load("http://uploaded.net/me")

            html = self.load("http://uploaded.net/io/login",
                             post={'id': user,
                                   'pw': password})

            m = re.search(r'"err":"(.+?)"', html)
            if m is not None:
                self.fail_login(m.group(1))

        except Exception, e:
            self.log_error(e.message, trace=True)
            self.fail_login(e.message)
