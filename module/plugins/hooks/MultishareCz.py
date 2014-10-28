# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL
from module.plugins.internal.MultiHoster import MultiHoster


class MultishareCz(MultiHoster):
    __name__ = "MultishareCz"
    __type__ = "hook"
    __version__ = "0.04"

    __config__ = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "uloz.to")]

    __description__ = """MultiShare.cz hook plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*?alt="([^"]+)"></td>\s*<td class="stav">[^>]*?alt="OK"'


    def getHoster(self):
        page = getURL("http://www.multishare.cz/monitoring/")
        return re.findall(self.HOSTER_PATTERN, page)
