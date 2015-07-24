# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class DodanePl(DeadHoster):
    __name__    = "DodanePl"
    __type__    = "hoster"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?dodane\.pl/file/\d+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Dodane.pl hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("z00nx", "z00nx0@gmail.com")]


getInfo = create_getInfo(DodanePl)
