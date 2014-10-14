# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from module.plugins.internal.XFSPAccount import XFSPAccount
from module.utils import parseFileSize


class RapidfileshareNet(XFSPAccount):
    __name__ = "RapidfileshareNet"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """Rapidfileshare.net account plugin"""
    __license__ = "GPLv3"
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_URL = "http://www.rapidfileshare.net/"

    TRAFFIC_LEFT_PATTERN = r'>Traffic available today:</TD><TD><label for="name">(?P<S>.+?)</label></TD></TR>'


    def loadAccountInfo(self, user, req):
        html = req.load(self.HOSTER_URL, get={'op': "my_account"}, decode=True)

        validuntil = None
        trafficleft = None
        premium = None

        if hasattr(self, "PREMIUM_PATTERN"):
            premium = True if re.search(self.PREMIUM_PATTERN, html) else False

        m = re.search(self.VALID_UNTIL_PATTERN, html)
        if m:
            expiredate = m.group(1)
            self.logDebug("Expire date: " + expiredate)

            try:
                validuntil = mktime(strptime(expiredate, "%d %B %Y"))
            except Exception, e:
                self.logError(e)
            else:
                if validuntil > mktime(gmtime()):
                    premium = True
                    trafficleft = -1
                else:
                    if premium is False:  #: registered account type (not premium)
                        validuntil = -1
                    premium = False

        try:
            traffic = re.search(self.TRAFFIC_LEFT_PATTERN, html).groupdict()
            trafficsize = traffic['S'] + traffic['U'] if 'U' in traffic else traffic['S']
            if "Unlimited" in trafficsize:
                trafficleft = -1
                if premium is None:
                    premium = True
            else:
                trafficleft = parseFileSize(trafficsize)/1024
        except:
            pass

        if premium is None:
            premium = False

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}
