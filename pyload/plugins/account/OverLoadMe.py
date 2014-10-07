# -*- coding: utf-8 -*-

from pyload.plugins.base.Account import Account
from pyload.utils import json_loads


class OverLoadMe(Account):
    __name__ = "OverLoadMe"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Over-Load.me account plugin"""
    __authors__ = [("marley", "marley@over-load.me")]


    def loadAccountInfo(self, user, req):
        data = self.getAccountData(user)
        page = req.load("https://api.over-load.me/account.php", get={"user": user, "auth": data['password']}).strip()
        data = json_loads(page)

        # Check for premium
        if data['membership'] == "Free":
            return {"premium": False}

        account_info = {"validuntil": data['expirationunix'], "trafficleft": -1}
        return account_info

    def login(self, user, data, req):
        jsondata = req.load("https://api.over-load.me/account.php",
                            get={"user": user, "auth": data['password']}).strip()
        data = json_loads(jsondata)

        if data['err'] == 1:
            self.wrongPassword()
