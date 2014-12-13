# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster, create_getInfo


class SpeedfileCz(DeadHoster):
    __name    = "SpeedFileCz"
    __type    = "hoster"
    __version = "0.32"

    __pattern = r'http://(?:www\.)?speedfile\.cz/.*'

    __description = """Speedfile.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(SpeedfileCz)
