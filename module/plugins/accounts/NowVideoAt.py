# -*- coding: utf-8 -*-

import re

from time import gmtime, mktime, strptime

from module.plugins.Account import Account


class NowVideoAt(Account):
    __name__    = "NowVideoAt"
    __type__    = "account"
    __version__ = "0.01"

    __description__ = """NowVideo.at account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    VALID_UNTIL_PATTERN = r'>Your premium membership expires on: (.+?)<'


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = -1
        premium     = None

        html = req.load("http://www.nowvideo.at/premium.php")

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1).strip()
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%Y-%b-%d"))

            except Exception, e:
                self.logError(e)

            else:
                if validuntil > mktime(gmtime()):
                    premium = True
                else:
                    premium = False
                    validuntil = -1

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}


    def login(self, user, data, req):
        html = req.load("http://www.nowvideo.at/login.php",
                        post={'user': user, 'pass': data['password']})

        if ">Invalid login details" is html:
            self.wrongPassword()
