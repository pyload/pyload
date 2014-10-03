# -*- coding: utf-8 -*-

import re

from time import mktime, strptime, gmtime

from pyload.plugins.Account import Account
from pyload.plugins.internal.SimpleHoster import parseHtmlForm
from pyload.utils import parseFileSize


class TusfilesNet(Account):
    __name__ = "TusfilesNet"
    __type__ = "account"
    __version__ = "0.01"

    __description__ = """ Tusfile.net account plugin """
    __author_name__ = "guidobelix"
    __author_mail__ = "guidobelix@hotmail.it"

    VALID_UNTIL_PATTERN = r'<span class="label label-default">([^<]+)</span>'
    TRAFFIC_LEFT_PATTERN = r'<td><img src="//www.tusfiles.net/i/icon/meter.png" alt=""/></td>\n<td>&nbsp;(?P<S>[^<]+)</td>'


    def loadAccountInfo(self, user, req):
        html = req.load("http://www.tusfiles.net/?op=my_account", decode=True)

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


    def login(self, user, data, req):
        html = req.load("http://www.tusfiles.net/login.html", decode=True)
        action, inputs = parseHtmlForm('name="FL"', html)
        inputs.update({'login': user,
                       'password': data['password'],
                       'redirect': "http://www.tusfiles.net/"})

        html = req.load("http://www.tusfiles.net/", post=inputs, decode=True)

        if 'Incorrect Login or Password' in html or '>Error<' in html:
            self.wrongPassword()
