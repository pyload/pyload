# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class DodanePl(DeadHoster):
    __name    = "DodanePl"
    __type    = "hoster"
    __version = "0.03"

    __pattern = r'http://(?:www\.)?dodane\.pl/file/\d+'

    __description = """Dodane.pl hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("z00nx", "z00nx0@gmail.com")]


getInfo = create_getInfo(DodanePl)
