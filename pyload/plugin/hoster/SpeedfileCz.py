# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class SpeedfileCz(DeadHoster):
    __name__    = "SpeedFileCz"
    __type__    = "hoster"
    __version__ = "0.32"

    __pattern__ = r'http://(?:www\.)?speedfile\.cz/.+'

    __description__ = """Speedfile.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]
