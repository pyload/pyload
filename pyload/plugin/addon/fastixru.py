# -*- coding: utf-8 -*-

# should be working

from __future__ import unicode_literals
from pyload.network.request import get_url
from pyload.plugin.internal.multihoster import MultiHoster
from pyload.common.json_layer import json_loads


class FastixRu(MultiHoster):
    __name__ = "FastixRu"
    __version__ = "0.02"
    __type__ = "hook"
    __config__ = [("activated", "bool", "Activated", False),
                  ("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                  ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                  ("interval", "int", "Reload interval in hours (0 to disable)", 24)]
    __description__ = """Fastix.ru hook plugin"""
    __author_name__ = "Massimo Rosamilia"
    __author_mail__ = "max@spiritix.eu"

    def get_hoster(self):
        page = get_url(
            "http://fastix.ru/api_v2/?apikey=5182964c3f8f9a7f0b00000a_kelmFB4n1IrnCDYuIFn2y&sub=allowed_sources")
        host_list = json_loads(page)
        host_list = host_list['allow']
        return host_list
