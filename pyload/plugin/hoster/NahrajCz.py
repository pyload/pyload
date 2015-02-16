# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class NahrajCz(DeadHoster):
    __name__    = "NahrajCz"
    __type__    = "hoster"
    __version__ = "0.21"

    __pattern__ = r'http://(?:www\.)?nahraj\.cz/content/download/.+'

    __description__ = """Nahraj.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
