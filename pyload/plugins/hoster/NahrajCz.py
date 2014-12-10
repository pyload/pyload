# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class NahrajCz(DeadHoster):
    __name    = "NahrajCz"
    __type    = "hoster"
    __version = "0.21"

    __pattern = r'http://(?:www\.)?nahraj\.cz/content/download/.+'

    __description = """Nahraj.cz hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(NahrajCz)
