# -*- coding: utf-8 -*-

import re

from module.plugins.Account import Account
from module.utils import parseFileSize


class StahnuTo(Account):
    __name__ = "StahnuTo"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """StahnuTo account plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.stahnu.to/")

        m = re.search(r'>VIP: (\d+.*)<', html)
        trafficleft = parseFileSize(m.group(1)) * 1024 if m else 0

        return {"premium": trafficleft > (512 * 1024), "trafficleft": trafficleft, "validuntil": -1}

    def login(self, user, data, req):
        html = req.load("http://www.stahnu.to/login.php", post={
            "username": user,
            "password": data['password'],
            "submit": "Login"})

        if not '<a href="logout.php">' in html:
            self.wrongPassword()
