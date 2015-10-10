# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class NahrajCz(DeadHoster):
    __name__    = "NahrajCz"
    __type__    = "hoster"
    __version__ = "0.22"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?nahraj\.cz/content/download/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Nahraj.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(NahrajCz)
