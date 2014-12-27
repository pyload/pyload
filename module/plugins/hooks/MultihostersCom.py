# -*- coding: utf-8 -*-

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster

class MultihostersCom(MultiHoster):
    __name__ = "MultihostersCom"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Multihosters.com hook plugin"""
    __author_name__ = "tjeh"
    __author_mail__ = "tjeh@gmx.net"

    def getHoster(self):
        page = getURL("http://www.multihosters.com/jDownloader.ashx?cmd=gethosters")
        return [x.strip() for x in page.split(",")]