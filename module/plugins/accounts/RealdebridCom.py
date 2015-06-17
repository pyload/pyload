# -*- coding: utf-8 -*-

import xml.dom.minidom

from module.plugins.internal.Account import Account


class RealdebridCom(Account):
    __name__    = "RealdebridCom"
    __type__    = "account"
    __version__ = "0.47"

    __description__ = """Real-Debrid.com account plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Devirex Hazzard", "naibaf_11@yahoo.de")]


    def loadAccountInfo(self, user, req):
        if self.pin_code:
            return

        html = req.load("https://real-debrid.com/api/account.php")
        account  = xml.dom.minidom.parseString(html)

        validuntil = float(account.getElementsByTagName("expiration")[0].childNodes[0].nodeValue)

        return {'validuntil' : validuntil,
                'trafficleft': -1        ,
                'premium'    : True      }


    def login(self, user, data, req):
        self.pin_code = False

        html = req.load("https://real-debrid.com/ajax/login.php",
                        get={"user": user, "pass": data['password']},
                        decode=True)

        if "Your login informations are incorrect" in html:
            self.wrongPassword()

        elif "PIN Code required" in html:
            self.logWarning(_("PIN code required. Please login to https://real-debrid.com using the PIN or disable the double authentication in your control panel on https://real-debrid.com"))
            self.pin_code = True
