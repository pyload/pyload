# -*- coding: utf-8 -*-

from pyload.utils import json_loads
from pyload.network.RequestFactory import getURL
from pyload.plugins.internal.MultiHoster import MultiHoster


class LinksnappyCom(MultiHoster):
    __name    = "LinksnappyCom"
    __type    = "hook"
    __version = "0.01"

    __config = [("hosterListMode", "all;listed;unlisted", "Use for hosters (if supported)", "all"),
                ("hosterList", "str", "Hoster list (comma separated)", ""),
                ("unloadFailing", "bool", "Revert to standard download if download fails", False),
                ("interval", "int", "Reload interval in hours (0 to disable)", 24)]

    __description = """Linksnappy.com hook plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    def getHoster(self):
        json_data = getURL("http://gen.linksnappy.com/lseAPI.php", get={'act': "FILEHOSTS"})
        json_data = json_loads(json_data)

        return json_data['return'].keys()
