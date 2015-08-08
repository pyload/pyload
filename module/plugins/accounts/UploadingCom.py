# -*- coding: utf-8 -*-

import re
import time

from module.plugins.internal.Account import Account
from module.plugins.internal.Plugin import set_cookies


class UploadingCom(Account):
    __name__    = "UploadingCom"
    __type__    = "account"
    __version__ = "0.14"
    __status__  = "testing"

    __description__ = """Uploading.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


    PREMIUM_PATTERN = r'UPGRADE TO PREMIUM'
    VALID_UNTIL_PATTERN = r'Valid Until:(.+?)<'


    def parse_info(self, user, password, data, req):
        validuntil  = None
        trafficleft = None
        premium     = None

        html = self.load("http://uploading.com/")

        premium = False if re.search(self.PREMIUM_PATTERN, html) else True

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.log_debug("Expire date: " + expiredate)

            try:
                validuntil = time.mktime(time.strptime(expiredate, "%b %d, %Y"))

            except Exception, e:
                self.log_error(e)

            else:
                if validuntil > time.mktime(time.gmtime()):
                    premium    = True
                else:
                    premium    = False
                    validuntil = None

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, password, data, req):
        set_cookies(req.cj,
                    [("uploading.com", "lang"    , "1" ),
                     ("uploading.com", "language", "1" ),
                     ("uploading.com", "setlang" , "en"),
                     ("uploading.com", "_lang"   , "en")])

        self.load("http://uploading.com/")
        self.load("https://uploading.com/general/login_form/?JsHttpRequest=%s-xml" % long(time.time() * 1000),
                  post={'email'   : user,
                        'password': password,
                        'remember': "on"})
