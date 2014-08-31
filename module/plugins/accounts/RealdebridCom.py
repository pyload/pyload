# -*- coding: utf-8 -*-

import xml.dom.minidom as dom

from module.plugins.Account import Account


class RealdebridCom(Account):
    __name__ = "RealdebridCom"
    __type__ = "account"
    __version__ = "0.43"

    __description__ = """Real-Debrid.com account plugin"""
    __author_name__ = "Devirex Hazzard"
    __author_mail__ = "naibaf_11@yahoo.de"


    def loadAccountInfo(self, user, req):
        if self.pin_code:
            return {"premium": False}
        page = req.load("https://real-debrid.com/api/account.php")
        xml = dom.parseString(page)
        account_info = {"validuntil": int(xml.getElementsByTagName("expiration")[0].childNodes[0].nodeValue),
                        "trafficleft": -1}

        return account_info

    def login(self, user, data, req):
        self.pin_code = False
        page = req.load("https://real-debrid.com/ajax/login.php", get={"user": user, "pass": data['password']})
        if "Your login informations are incorrect" in page:
            self.wrongPassword()
        elif "PIN Code required" in page:
            self.logWarning('PIN code required. Please login to https://real-debrid.com using the PIN or disable the double authentication in your control panel on https://real-debrid.com.')
            self.pin_code = True
