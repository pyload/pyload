# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class StorageTo(DeadHoster):
    __name__    = "StorageTo"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?storage\.to/get/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Storage.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("mkaay", "mkaay@mkaay.de")]


getInfo = create_getInfo(StorageTo)
