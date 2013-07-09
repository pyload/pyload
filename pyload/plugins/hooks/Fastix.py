# -*- coding: utf-8 -*-

# should be working

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class Fastix(MultiHoster):
    __name__ = "Fastix"
    __version__ = "0.01"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", "False"),
                  ("interval", "int", "Reload interval in hours (0 to disable)", "24")]

    __description__ = """Fastix hook plugin"""
    __author_name__ = ("Massimo, Rosamilia")
    __author_mail__ = ("max@spiritix.eu")

    def getHoster(self):
        page = getURL("http://fastix.ru/api_v2/?apikey=5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y&sub=allowed_sources")
        page = page.split('],"request":')
        page = page[0]
        page = page.split('{"allow":[')
        page = page[1]
        page = page.replace("\"","").strip()
        return [x.strip() for x in page.split(",") if x.strip()]
