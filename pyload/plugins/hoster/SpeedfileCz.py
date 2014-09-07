# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SpeedfileCz(DeadHoster):
    __name__ = "SpeedFileCz"
    __type__ = "hoster"
    __version__ = "0.32"

    __pattern__ = r'http://(?:www\.)?speedfile.cz/.*'

    __description__ = """Speedfile.cz hoster plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


getInfo = create_getInfo(SpeedfileCz)
