# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class IcyFilesCom(DeadHoster):
    __name__    = "IcyFilesCom"
    __type__    = "hoster"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?icyfiles\.com/(.+)'
    __config__  = []

    __description__ = """IcyFiles.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("godofdream", "soilfiction@gmail.com")]
