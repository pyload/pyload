# -*- coding: utf-8 -*-

import re
from time import time

from module.plugins.Account import Account


class NetloadIn(Account):
    __name__ = "NetloadIn"
    __type__ = "account"
    __version__ = "0.22"

    __description__ = """Netload.in account plugin"""
    __author_name__ = ("RaNaN", "CryNickSystems")
    __author_mail__ = ("RaNaN@pyload.org", "webmaster@pcProfil.de")


    def loadAccountInfo(self, user, req):
        page = req.load("http://netload.in/index.php?id=2&lang=de")
        left = r">(\d+) (Tag|Tage), (\d+) Stunden<"
        left = re.search(left, page)
        if left:
            validuntil = time() + int(left.group(1)) * 24 * 60 * 60 + int(left.group(3)) * 60 * 60
            trafficleft = -1
            premium = True
        else:
            validuntil = None
            premium = False
            trafficleft = None
        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}

    def login(self, user, data, req):
        page = req.load("http://netload.in/index.php", None,
                        {"txtuser": user, "txtpass": data['password'], "txtcheck": "login", "txtlogin": "Login"},
                        cookies=True)
        if "password or it might be invalid!" in page:
            self.wrongPassword()
