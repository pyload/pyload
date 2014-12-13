# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugin.internal.MultiHoster import MultiHoster


class SimplydebridCom(MultiHoster):
    __name    = "SimplydebridCom"
    __type    = "hook"
    __version = "0.01"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description = """Simply-Debrid.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("Kagenoshin", "kagenoshin@gmx.ch")]


    def getHoster(self):
        page = getURL("http://simply-debrid.com/api.php", get={'list': 1})
        return [x.strip() for x in page.rstrip(';').replace("\"", "").split(";")]
