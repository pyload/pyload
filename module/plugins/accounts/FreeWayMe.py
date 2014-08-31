# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class FreeWayMe(Account):
    __name__ = "FreeWayMe"
    __type__ = "account"
    __version__ = "0.11"

    __description__ = """FreeWayMe account plugin"""
    __author_name__ = "Nicolas Giese"
    __author_mail__ = "james@free-way.me"


    def loadAccountInfo(self, user, req):
        status = self.getAccountStatus(user, req)
        if not status:
            return False
        self.logDebug(status)

        account_info = {"validuntil": -1, "premium": False}
        if status['premium'] == "Free":
            account_info['trafficleft'] = int(status['guthaben']) * 1024
        elif status['premium'] == "Spender":
            account_info['trafficleft'] = -1
        elif status['premium'] == "Flatrate":
            account_info = {"validuntil": int(status['Flatrate']),
                            "trafficleft": -1,
                            "premium": True}

        return account_info

    def getpw(self, user):
        return self.accounts[user]['password']

    def login(self, user, data, req):
        status = self.getAccountStatus(user, req)

        # Check if user and password are valid
        if not status:
            self.wrongPassword()

    def getAccountStatus(self, user, req):
        answer = req.load("https://www.free-way.me/ajax/jd.php",
                          get={"id": 4, "user": user, "pass": self.accounts[user]['password']})
        self.logDebug("login: %s" % answer)
        if answer == "Invalid login":
            self.wrongPassword()
            return False
        return json_loads(answer)
