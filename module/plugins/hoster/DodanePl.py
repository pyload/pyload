# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class DodanePl(DeadHoster):
    __name__    = "DodanePl"
    __type__    = "hoster"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?dodane\.pl/file/\d+'

    __description__ = """Dodane.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("z00nx", "z00nx0@gmail.com")]


getInfo = create_getInfo(DodanePl)
