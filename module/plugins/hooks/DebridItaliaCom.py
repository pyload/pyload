# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class DebridItaliaCom(MultiHook):
    __name__    = "DebridItaliaCom"
    __type__    = "hook"
    __version__ = "0.11"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", ""),
                  ("revertfailed", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Debriditalia.com hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    def getHosters(self):
        return self.getURL("http://debriditalia.com/api.php", get={'hosts': ""}).replace('"', '').split(',')
