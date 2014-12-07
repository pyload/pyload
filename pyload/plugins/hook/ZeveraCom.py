# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class ZeveraCom(MultiHoster):
    __name__    = "ZeveraCom"
    __type__    = "hook"
    __version__ = "0.02"

    __config__ = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description__ = """Real-Debrid.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def getHoster(self):
        page = getURL("http://www.zevera.com/jDownloader.ashx", get={'cmd': "gethosters"})
        return [x.strip() for x in page.replace("\"", "").split(",")]
