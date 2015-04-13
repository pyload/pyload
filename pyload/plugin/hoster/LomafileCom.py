# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class LomafileCom(DeadHoster):
    __name    = "LomafileCom"
    __type    = "hoster"
    __version = "0.52"

    __pattern = r'http://lomafile\.com/\w{12}'
    __config  = []

    __description = """Lomafile.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                       ("guidobelix", "guidobelix@hotmail.it")]
