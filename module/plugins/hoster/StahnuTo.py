# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class StahnuTo(DeadHoster):
    __name__    = "StahnuTo"
    __type__    = "hoster"
    __version__ = "0.14"
    __status__  = "stable"

    __pattern__ = r"http://(\w*\.)?stahnu.to/(files/get/|.*\?file=)([^/]+).*"
    __config__  = []

    __description__ = """Stahnu.to hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", None)]


getInfo = create_getInfo(StahnuTo)
