# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Pawel W. <dev@rapideo.pl>
"""

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

class RapideoPl(Account):
    __name__ = "RapideoPl"
    __version__ = "0.01"
    __type__ = "account"
    __description__ = "Rapideo.pl account plugin"
    __author_name__ = ("goddie")
    __author_mail__ = ("dev@rapideo.pl")

    _api_url = "http://enc.rapideo.pl"

    _api_query = {
        "site": "newrd",
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
            #todo: ret?
            return

        premium = False
        valid_untill = -1

        is_premium = "expire" in result.keys() and result["expire"] is not None

        if is_premium:

            premium = True
            valid_untill = mktime(datetime.fromtimestamp(int(result["expire"])).timetuple())

        traffic_left = result["balance"]

        return ({
            "validuntil": valid_untill,
            "trafficleft": traffic_left,
            "premium": premium
        })

    def login(self, user, data, req):

        self._usr = user
        self._pwd = crypto.md5(data["password"]).hexdigest()

        self._req = req

        try:
            response = loads(self.runAuthQuery())
        except:
            self.wrongPassword()

        if "errno" in response.keys():
            self.wrongPassword()

        data['usr'] = user
        data['pwd'] = crypto.md5(data['password']).hexdigest()

    def createAuthQuery(self):

        query = self._api_query
        query["username"] = self._usr
        query["password"] = self._pwd

        return query

    def runAuthQuery(self):

        data = self._req.load(self._api_url, post=self.createAuthQuery())

        return data