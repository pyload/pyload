# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class StorageTo(DeadHoster):
    __name    = "StorageTo"
    __type    = "hoster"
    __version = "0.01"

    __pattern = r'http://(?:www\.)?storage\.to/get/.+'
    __config  = []

    __description = """Storage.to hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]
