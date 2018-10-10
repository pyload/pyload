# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class IcyFilesCom(DeadHoster):
    __name__ = "IcyFilesCom"
    __type__ = "hoster"
    __version__ = "0.11"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?icyfiles\.com/(.+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """IcyFiles.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("godofdream", "soilfiction@gmail.com")]
