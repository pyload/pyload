# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from module.plugins.internal.XFSPAccount import XFSPAccount


class EasybytezCom(XFSPAccount):
    __name__    = "EasybytezCom"
    __type__    = "account"
    __version__ = "0.08"

    __description__ = """EasyBytez.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz"),
                       ("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_NAME = "easybytez.com"


    def loadAccountInfo(self, user, req):
        html = req.load(self.HOSTER_URL, get={'op': "my_account"}, decode=True)

        validuntil = None
        trafficleft = None
        premium = False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1)
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%d %B %Y"))
            except Exception, e:
                self.logError(e)

            if validuntil > mktime(gmtime()):
                premium = True
                trafficleft = -1
            else:
                premium = False
                validuntil = -1

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = m.group(1)
            if "Unlimited" in trafficleft:
                trafficleft = -1
            else:
                trafficleft = self.parseTraffic(trafficleft)

        return {"validuntil": validuntil, "trafficleft": trafficleft, "premium": premium}
