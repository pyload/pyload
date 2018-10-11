# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster


class LomafileCom(DeadHoster):
    __name__ = "LomafileCom"
    __type__ = "hoster"
    __version__ = "0.57"
    __status__ = "stable"

    __pattern__ = r'http://lomafile\.com/\w{12}'
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Lomafile.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                   ("guidobelix", "guidobelix@hotmail.it")]
