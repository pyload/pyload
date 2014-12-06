# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class DebridItaliaCom(MultiHoster):
    __name__    = "DebridItaliaCom"
    __type__    = "hook"
    __version__ = "0.08"

    __config__ = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Debriditalia.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def getHoster(self):
        html = getURL("http://www.debriditalia.com/status.php")
        return re.findall(r'title="(.+?)"> \1</td><td><img src="/images/(?:attivo|testing)', html)
