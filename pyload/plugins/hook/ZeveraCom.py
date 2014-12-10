# -*- coding: utf-8 -*-

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class ZeveraCom(MultiHoster):
    __name    = "ZeveraCom"
    __type    = "hook"
    __version = "0.02"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description = """Real-Debrid.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def getHoster(self):
        page = getURL("http://www.zevera.com/jDownloader.ashx", get={'cmd': "gethosters"})
        return [x.strip() for x in page.replace("\"", "").split(",")]
