# -*- coding: utf-8 -*-

import re
import time

from module.plugins.Account import Account
from module.utils import parseFileSize


class FilerNet(Account):
    __name__ = "FilerNet"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Filer.net account plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    TOKEN_PATTERN = r'_csrf_token" value="([^"]+)" />'
    WALID_UNTIL_PATTERN = r"Der Premium-Zugang ist gültig bis (.+)\.\s*</td>"
    TRAFFIC_PATTERN = r'Traffic</th>\s*<td>([^<]+)</td>'
    FREE_PATTERN = r'Account Status</th>\s*<td>\s*Free'


    def loadAccountInfo(self, user, req):
        html = req.load("https://filer.net/profile")

        # Free user
        if re.search(self.FREE_PATTERN, html):
            return {"premium": False, "validuntil": None, "trafficleft": None}

        until = re.search(self.WALID_UNTIL_PATTERN, html)
        traffic = re.search(self.TRAFFIC_PATTERN, html)
        if until and traffic:
            validuntil = int(time.mktime(time.strptime(until.group(1), "%d.%m.%Y %H:%M:%S")))
            trafficleft = parseFileSize(traffic.group(1)) / 1024
            return {"premium": True, "validuntil": validuntil, "trafficleft": trafficleft}
        else:
            self.logError('Unable to retrieve account information - Plugin may be out of date')
            return {"premium": False, "validuntil": None, "trafficleft": None}

    def login(self, user, data, req):
        html = req.load("https://filer.net/login")
        token = re.search(self.TOKEN_PATTERN, html).group(1)
        html = req.load("https://filer.net/login_check",
                             post={"_username": user, "_password": data['password'],
                                   "_remember_me": "on", "_csrf_token": token, "_target_path": "https://filer.net/"})
        if 'Logout' not in html:
            self.wrongPassword()
