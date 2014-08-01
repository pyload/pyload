# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class ZeveraCom(MultiHoster):
    __name__ = "ZeveraCom"
    __type__ = "hook"
    __version__ = "0.02"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "")]

    __description__ = """Real-Debrid.com hook plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def getHoster(self):
        page = getURL("http://www.zevera.com/jDownloader.ashx?cmd=gethosters")
        return [x.strip() for x in page.replace("\"", "").split(",")]
