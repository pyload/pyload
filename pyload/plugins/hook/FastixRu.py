# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class FastixRu(MultiHoster):
    __name__ = "FastixRu"
    __type__ = "addon"
    __version__ = "0.02"

    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description__ = """Fastix.ru addon plugin"""
    __author_name__ = "Massimo Rosamilia"
    __author_mail__ = "max@spiritix.eu"


    def getHoster(self):
        page = getURL(
            "http://fastix.ru/api_v2/?apikey=5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y&sub=allowed_sources")
        host_list = json_loads(page)
        host_list = host_list['allow']
        return host_list
