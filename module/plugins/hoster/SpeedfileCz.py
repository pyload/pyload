# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class SpeedfileCz(DeadHoster):
    __name__ = "SpeedFileCz"
    __type__ = "hoster"
    __version__ = "0.37"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?speedfile\.cz/.+'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Speedfile.cz hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
