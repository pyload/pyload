# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import re

from pyload.network.requestfactory import get_url
from pyload.plugin.internal.multihoster import MultiHoster


class MultishareCz(MultiHoster):
    __name__ = "MultishareCz"
    __version__ = "0.04"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", "uloz.to")]
    __description__ = """MultiShare.cz hook plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    HOSTER_PATTERN = r'<img class="logo-shareserveru"[^>]*?alt="([^"]+)"></td>\s*<td class="stav">[^>]*?alt="OK"'

    def get_hoster(self):
        page = get_url("http://www.multishare.cz/monitoring/")
        return re.findall(self.HOSTER_PATTERN, page)
