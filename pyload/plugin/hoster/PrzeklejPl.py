# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class PrzeklejPl(DeadHoster):
    __name    = "PrzeklejPl"
    __type    = "hoster"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?przeklej\.pl/plik/.+'

    __description = """Przeklej.pl hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(PrzeklejPl)
