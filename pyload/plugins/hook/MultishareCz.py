# -*- coding: utf-8 -*-

import re

from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class MultishareCz(MultiHoster):
    __name    = "MultishareCz"
    __type    = "hook"
    __version = "0.04"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", "uloz.to")]

    __description = """MultiShare.cz hook plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*?alt="([^"]+)"></td>\s*<td class="stav">[^>]*?alt="OK"'


    def getHoster(self):
        page = getURL("http://www.multishare.cz/monitoring/")
        return re.findall(self.HOSTER_PATTERN, page)
