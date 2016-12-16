# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyload.network.requestfactory import get_url
from pyload.plugins.internal.multihoster import MultiHoster


class OverLoadMe(MultiHoster):
    __name__ = "OverLoadMe"
    __version__ = "0.01"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", False),
                  ("https", "bool", "Enable HTTPS", True),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported):", "all"),
                  ("hosterList", "str", "Hoster list (comma separated)", ""),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 12)]
    __description__ = """Over-Load.me hook plugin"""
    __author_name__ = "marley"
    __author_mail__ = "marley@over-load.me"

    def get_hoster(self):
        https = "https" if self.get_config("https") else "http"
        page = get_url(https + "://api.over-load.me/hoster.php",
                      get={"auth": "0001-cb1f24dadb3aa487bda5afd3b76298935329be7700cd7-5329be77-00cf-1ca0135f"}
                      ).replace("\"", "").strip()
        self.log_debug("Hosterlist: %s" % page)

        return [x.strip() for x in page.split(",") if x.strip()]
