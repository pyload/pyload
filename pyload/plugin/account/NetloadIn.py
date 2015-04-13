# -*- coding: utf-8 -*-

import re
import time

from pyload.plugin.Account import Account


class NetloadIn(Account):
    __name    = "NetloadIn"
    __type    = "account"
    __version = "0.24"

    __description = """Netload.in account plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def api_response(self, id, password, req):
        return req.load("http://api.netload.in/user_info.php",
                        get={'auth'         : "BVm96BWDSoB4WkfbEhn42HgnjIe1ilMt",
                             'user_id'      : id,
                             'user_password': password}).strip()


    def loadAccountInfo(self, user, req):
        validuntil  = None
        trafficleft = -1
        premium     = False

        html = self.api_response(user, self.getAccountData(user)['password'], req)

        if html == "-1":
            premium = True

        elif html == "0":
            validuntil = -1

        else:
            try:
                validuntil = time.mktime(time.strptime(html, "%Y-%m-%d %H:%M"))

            except Exception, e:
                self.logError(e)

            else:
                self.logDebug("Valid until: %s" % validuntil)

                if validuntil > time.mktime(time.gmtime()):
                    premium = True
                else:
                    validuntil = -1

        return {'validuntil' : validuntil,
                'trafficleft': trafficleft,
                'premium'    : premium}


    def login(self, user, data, req):
        html = self.api_response(user, data['password'], req)

        if not html or re.search(r'disallowed_agent|unknown_auth|login_failed', html):
            self.wrongPassword()
