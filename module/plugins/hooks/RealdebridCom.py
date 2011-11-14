# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class RealdebridCom(MultiHoster):
    __name__ = "RealdebridCom"
    __version__ = "0.4"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("https", "bool", "Enable HTTPS", "False")]

    __description__ = """Real-Debrid.com hook plugin"""
    __author_name__ = ("Devirex, Hazzard")
    __author_mail__ = ("naibaf_11@yahoo.de")

    replacements = [("freakshare.net", "freakshare.com")]

    def getHoster(self):
        https = "https" if self.getConfig("https") else "http"
        page = getURL(https + "://real-debrid.com/api/hosters.php").replace("\"","").strip()

        return[x.strip() for x in page.split(",") if x.strip()]