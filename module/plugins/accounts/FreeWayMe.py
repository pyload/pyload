# -*- coding: utf-8 -*-

from module.plugins.Account import Account
from module.common.json_layer import json_loads


class FreeWayMe(Account):
    __name__    = "FreeWayMe"
    __type__    = "account"
    __version__ = "0.14"

    __description__ = """FreeWayMe account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Nicolas Giese", "james@free-way.me")]


    def loadAccountInfo(self, user, req):
        status = self.getAccountStatus(user, req)

        self.logDebug(status)

        account_info = {"validuntil": -1, "premium": False}
        if status['premium'] == "Free":
            account_info['trafficleft'] = self.parseTraffic(status['guthaben'] + "MB")
        elif status['premium'] == "Spender":
            account_info['trafficleft'] = -1
        elif status['premium'] == "Flatrate":
            account_info = {"validuntil": float(status['Flatrate']),
                            "trafficleft": -1,
                            "premium": True}

        return account_info


    def login(self, user, data, req):
        status = self.getAccountStatus(user, req)

        # Check if user and password are valid
        if not status:
            self.wrongPassword()


    def getAccountStatus(self, user, req):
        answer = req.load("http://www.free-way.bz/ajax/jd.php",  #@TODO: Revert to `https` in 0.4.10
                          get={"id": 4, "user": user, "pass": self.getAccountData(user)['password']})

        self.logDebug("Login: %s" % answer)

        if answer == "Invalid login":
            self.wrongPassword()

        return json_loads(answer)
