# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class PrzeklejPl(DeadHoster):
    __name__    = "PrzeklejPl"
    __type__    = "hoster"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?przeklej\.pl/plik/.+'
    __config__  = []

    __description__ = """Przeklej.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
