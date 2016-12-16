# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.network.requestfactory import get_url
from pyload.plugin.internal.multihoster import MultiHoster


class RealdebridCom(MultiHoster):
    __name__ = "RealdebridCom"
    __version__ = "0.43"
    __type__ = "hook"

    __config__ = [("activated", "bool", "Activated", False),
                  ("https", "bool", "Enable HTTPS", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to stanard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]
    __description__ = """Real-Debrid.com hook plugin"""
    __author_name__ = "Devirex Hazzard"
    __author_mail__ = "naibaf_11@yahoo.de"

    def get_hoster(self):
        https = "https" if self.get_config("https") else "http"
        page = get_url(https + "://real-debrid.com/api/hosters.php").replace("\"", "").strip()

        return [x.strip() for x in page.split(",") if x.strip()]
