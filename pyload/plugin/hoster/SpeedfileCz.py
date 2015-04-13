# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class SpeedfileCz(DeadHoster):
    __name    = "SpeedFileCz"
    __type    = "hoster"
    __version = "0.32"

    __pattern = r'http://(?:www\.)?speedfile\.cz/.+'
    __config  = []

    __description = """Speedfile.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]
