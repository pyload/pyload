# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class SimplydebridCom(MultiHoster):
    __name__    = "SimplydebridCom"
    __type__    = "hook"
    __version__ = "0.01"

    __config__ = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description__ = """Simply-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def getHoster(self):
        page = getURL("http://simply-debrid.com/api.php?list=1")
        return [x.strip() for x in page.rstrip(';').replace("\"", "").split(";")]
