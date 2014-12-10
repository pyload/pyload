# -*- coding: utf-8 -*-

from pyload.plugins.Plugin import Plugin


def getInfo(self):
        #result = [ .. (name, size, status, url) .. ]
        return


class Hoster(Plugin):
    __name    = "Hoster"
    __type    = "hoster"
    __version = "0.02"

    __pattern = r'^unmatchable$'
    __config  = []  #: [("name", "type", "desc", "default")]

    __description = """Base hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("mkaay", "mkaay@mkaay.de")]
