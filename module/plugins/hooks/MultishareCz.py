# -*- coding: utf-8 -*-

import re

from module.plugins.internal.MultiHook import MultiHook


class MultishareCz(MultiHook):
    __name__    = "MultishareCz"
    __type__    = "hook"
    __version__ = "0.06"

    __config__ = [("mode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("pluginlist", "str", "Hoster list (comma separated)", "uloz.to")]

    __description__ = """MultiShare.cz hook plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*?alt="([^"]+)"></td>\s*<td class="stav">[^>]*?alt="OK"'


    def getHosters(self):
        page = self.getURL("http://www.multishare.cz/monitoring/")
        return re.findall(self.HOSTER_PATTERN, page)
