# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class TurbouploadCom(DeadHoster):
    __name__ = "TurbouploadCom"
    __type__ = "hoster"
    __version__ = "0.08"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?turboupload\.com/(\w+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Turboupload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
