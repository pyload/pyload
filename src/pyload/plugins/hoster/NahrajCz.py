# -*- coding: utf-8 -*-

from pyload.plugins.internal.deadhoster import DeadHoster


class NahrajCz(DeadHoster):
    __name__ = "NahrajCz"
    __type__ = "hoster"
    __version__ = "0.26"
    __status__ = "stable"

    __pattern__ = r"http://(?:www\.)?nahraj\.cz/content/download/.+"
    __config__ = []  # TODO: Remove in 0.6.x

    __description__ = """Nahraj.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
