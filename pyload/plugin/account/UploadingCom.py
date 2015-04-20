# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account
from pyload.plugin.internal.SimpleHoster import set_cookies


class UploadingCom(Account):
    __name    = "UploadingCom"
    __type    = "account"
    __version = "0.12"

    __description = """Uploading.com account plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]


    PREMIUM_PATTERN = r'UPGRADE TO PREMIUM'
    VALID_UNTIL_PATTERN = r'Valid Until:(.+?)<'


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = None
        premium     = None

        html = req.load("http://uploading.com/")

        premium = re.search(self.PREMIUM_PATTERN, html) is None

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = time.mktime(time.strptime(expiredate, "%b %d, %Y"))

            except Exception, e:
                self.logError(e)

            else:
                if validuntil > time.mktime(time.gmtime()):
                    premium    = True
                else:
                    premium    = False
                    validuntil = None

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, data, req):
        set_cookies(req.cj,
                    [("uploading.com", "lang"    , "1" ),
                     ("uploading.com", "language", "1" ),
                     ("uploading.com", "setlang" , "en"),
                     ("uploading.com", "_lang"   , "en")])

        req.load("http://uploading.com/")
        req.load("http://uploading.com/general/login_form/?JsHttpRequest=%s-xml" % long(time.time() * 1000),
                 post={'email': user, 'password': data['password'], 'remember': "on"})
