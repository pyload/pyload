# -*- coding: utf-8 -*-

import re

from pyload.plugin.Account import Account
from pyload.utils import json_loads


class RapiduNet(Account):
    __name    = "RapiduNet"
    __type    = "account"
    __version = "0.02"

    __description = """Rapidu.net account plugin"""
    __license     = "GPLv3"
    __authors     = [("prOq", "")]


    PREMIUM_PATTERN = r'<a href="premium/" style="padding-left: 0px;">Account: <b>Premium</b></a>'


    def loadAccountInfo(self, user, req):
        info = {'validuntil': None, 'trafficleft': None, 'premium': False}

        req.load("https://rapidu.net/ajax.php", get={'a': "getChangeLang"}, post={"_go": "", "lang": "en"})
        html = req.load("https://rapidu.net/", decode=True)

        if re.search(self.PREMIUM_PATTERN, html):
            info['premium'] = True

        return info


    def login(self, user, data, req):
        try:
            json = json_loads(req.load("https://rapidu.net/ajax.php?a=getUserLogin",
                                       post={'_go': "",
                                             'login': user,
                                             'pass': data['password'],
                                             'member': "1"}))

            self.logDebug(json)

            if not json['message'] == "success":
                self.wrongPassword()

        except Exception, e:
            self.logError(e)
