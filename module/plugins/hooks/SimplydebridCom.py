# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class SimplydebridCom(MultiHoster):
    __name__ = "SimplydebridCom"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", "False"),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]
    __description__ = """Simply-Debrid.com hook plugin"""
    __author_name__ = ("Kagenoshin")
    __author_mail__ = ("kagenoshin@gmx.ch")

    def getHoster(self):
        page = getURL("http://simply-debrid.com/api.php?list=1")
        return [x.strip() for x in page.rstrip(';').replace("\"", "").split(";")]
