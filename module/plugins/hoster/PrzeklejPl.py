# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class PrzeklejPl(DeadHoster):
    __name__    = "PrzeklejPl"
    __type__    = "hoster"
    __version__ = "0.14"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?przeklej\.pl/plik/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Przeklej.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(PrzeklejPl)
