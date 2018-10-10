# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class EnteruploadCom(DeadHoster):
    __name__ = "EnteruploadCom"
    __type__ = "hoster"
    __version__ = "0.07"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?enterupload\.com/\w+'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """EnterUpload.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
