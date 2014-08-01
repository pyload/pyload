# -*- coding: utf-8 -*-

from module.plugins.Plugin import Plugin


def getInfo(self):
        #result = [ .. (name, size, status, url) .. ]
        return


class Hoster(Plugin):
    __name__ = "Hoster"
    __type__ = "hoster"
    __version__ = "0.1"

    __pattern__ = None

    __description__ = """Base hoster plugin"""
    __author_name__ = "mkaay"
    __author_mail__ = "mkaay@mkaay.de"
