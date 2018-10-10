# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class StahnuTo(DeadHoster):
    __name__ = "StahnuTo"
    __type__ = "hoster"
    __version__ = "0.16"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?stahnu\.to/(files/get/|.*\?file=)([^/]+).*'
    __config__ = []

    __description__ = """Stahnu.to hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", None)]
