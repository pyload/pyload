# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHook import MultiHook


class DebridItaliaCom(MultiHook):
    __name__    = "DebridItaliaCom"
    __type__    = "hook"
    __version__ = "0.10"

    __config__ = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Debriditalia.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def getHoster(self):
        return getURL("http://debriditalia.com/api.php", get={'hosts': ""}).replace('"', '').split(',')
