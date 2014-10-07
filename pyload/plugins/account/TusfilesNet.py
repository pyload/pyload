# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from pyload.plugins.internal.XFSPAccount import XFSPAccount
from pyload.utils import parseFileSize


class TusfilesNet(XFSPAccount):
    __name__ = "TusfilesNet"
    __type__ = "account"
    __version__ = "0.02"

    __description__ = """Tusfile.net account plugin"""
    __authors__ = [("guidobelix", "guidobelix@hotmail.it")]


    HOSTER_URL = "http://www.tusfiles.net/"

    VALID_UNTIL_PATTERN = r'<span class="label label-default">([^<]+)</span>'
    TRAFFIC_LEFT_PATTERN = r'<td><img src="//www.tusfiles.net/i/icon/meter.png" alt=""/></td>\n<td>&nbsp;(?P<S>[^<]+)</td>'


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
            else:
                premium = False
                validuntil = None

        m = re.search(self.TRAFFIC_LEFT_PATTERN, html)
        if m:
            trafficleft = m.group(1)
            if "Unlimited" in trafficleft:
                trafficleft = -1
            else:
                trafficleft = parseFileSize(trafficleft) * 1024

        return {'validuntil': validuntil, 'trafficleft': trafficleft, 'premium': premium}
