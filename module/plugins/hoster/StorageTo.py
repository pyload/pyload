# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class StorageTo(DeadHoster):
    __name__    = "StorageTo"
    __type__    = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?storage\.to/get/.+'

    __description__ = """Storage.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(StorageTo)
