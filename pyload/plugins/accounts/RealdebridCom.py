#!/usr/bin/env python
# -*- coding: utf-8 -*-

from module.plugins.MultiHoster import MultiHoster
import xml.dom.minidom as dom

class RealdebridCom(MultiHoster):
    __name__ = "RealdebridCom"
    __version__ = "0.5"
    __type__ = "account"
    __description__ = """Real-Debrid.com account plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    def loadAccountInfo(self, req):
        page = req.load("http://real-debrid.com/api/account.php")
        xml = dom.parseString(page)
        account_info = {"validuntil": int(xml.getElementsByTagName("expiration")[0].childNodes[0].nodeValue),
                        "trafficleft": -1}

        return account_info

    def login(self, req):
        page = req.load("https://real-debrid.com/ajax/login.php?user=%s&pass=%s" % (self.loginname, self.password))
        #page = req.load("https://real-debrid.com/login.html", post={"user": user, "pass": data["password"]}, cookies=True)

        if "Your login informations are incorrect" in page:
            self.wrongPassword()


    def loadHosterList(self, req):
        https = "https" if self.getConfig("https") else "http"
        page = req.load(https + "://real-debrid.com/api/hosters.php").replace("\"","").strip()

        return[x.strip() for x in page.split(",") if x.strip()]