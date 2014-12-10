# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class DebridItaliaCom(MultiHoster):
    __name    = "DebridItaliaCom"
    __type    = "hook"
    __version = "0.08"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description = """Debriditalia.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def getHoster(self):
        html = getURL("http://www.debriditalia.com/status.php")
        return re.findall(r'title="(.+?)"> \1</td><td><img src="/images/(?:attivo|testing)', html)
