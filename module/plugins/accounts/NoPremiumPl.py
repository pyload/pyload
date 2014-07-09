# -*- coding: utf-8 -*-

from datetime import datetime

from module.plugins.Account import Account
from module.plugins.internal.SimpleHoster import parseHtmlForm
import re
from time import mktime, strptime
import module.lib.beaker.crypto as crypto

try:
    from json import loads
except ImportError:
    from simplejson import loads

class NoPremiumPl(Account):
    __name__ = "NoPremiumPl"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = "NoPremium.pl account plugin"
    __author_name__ = ("goddie")
    __author_mail__ = ("dev@nopremium.pl")

    _api_url = "http://crypt.nopremium.pl"

    _api_query = {
        "site": "nopremium",
        "username": "",
        "password": "",
        "output": "json",
        "loc": "1",
        "info": "1"
    }

    _req = None
    _usr = None
    _pwd = None

    def loadAccountInfo(self, name, req):

        self._req = req

        try:
            result = loads(self.runAuthQuery())
        except:
            #todo: return or let it be thrown?
            return

        premium = False
        valid_untill = -1

        is_premium = "expire" in result.keys() and result["expire"] is not None

        if is_premium:

            premium = True
            valid_untill = mktime(datetime.fromtimestamp(int(result["expire"])).timetuple())

        traffic_left = result["balance"] * 1024

        return ({
            "validuntil": valid_untill,
            "trafficleft": traffic_left,
            "premium": premium
        })

    def login(self, user, data, req):

        self._usr = user
        self._pwd = crypto.sha1(crypto.md5(data["password"]).hexdigest()).hexdigest()

        self._req = req

        try:
            response = loads(self.runAuthQuery())
        except:
            self.wrongPassword()

        if "errno" in response.keys():
            self.wrongPassword()

        data['usr'] = self._usr
        data['pwd'] = self._pwd

    def createAuthQuery(self):

        query = self._api_query
        query["username"] = self._usr
        query["password"] = self._pwd

        return query

    def runAuthQuery(self):

        data = self._req.load(self._api_url, post=self.createAuthQuery())

        return data