# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster


class IcyFilesCom(DeadHoster):
    __name__ = "IcyFilesCom"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?icyfiles\.com/(.+)'
    __config__ = []  # @TODO: Remove in 0.6.x

    __description__ = """IcyFiles.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
