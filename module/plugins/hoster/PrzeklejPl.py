# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class PrzeklejPl(DeadHoster):
    __name__    = "PrzeklejPl"
    __type__    = "hoster"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?przeklej\.pl/plik/.+'

    __description__ = """Przeklej.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(PrzeklejPl)
