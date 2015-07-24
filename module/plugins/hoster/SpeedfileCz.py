# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class SpeedfileCz(DeadHoster):
    __name__    = "SpeedFileCz"
    __type__    = "hoster"
    __version__ = "0.33"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?speedfile\.cz/.+'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """Speedfile.cz hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(SpeedfileCz)
