# -*- coding: utf-8 -*-

import re

from module.plugins.Account import Account


class StahnuTo(Account):
    __name__ = "StahnuTo"
    __type__ = "account"
    __version__ = "0.03"

    __description__ = """StahnuTo account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.stahnu.to/")

        m = re.search(r'>VIP: (\d+.*)<', html)
        trafficleft = self.parseTraffic(m.group(1)) * 1024 if m else 0

        return {"premium": trafficleft > (512 * 1024), "trafficleft": trafficleft, "validuntil": -1}


    def login(self, user, data, req):
        html = req.load("http://www.stahnu.to/login.php", post={
            "username": user,
            "password": data['password'],
            "submit": "Login"})

        if not '<a href="logout.php">' in html:
            self.wrongPassword()
