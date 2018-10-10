# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class UploadhereCom(DeadHoster):
    __name__ = "UploadhereCom"
    __type__ = "hoster"
    __version__ = "0.17"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?uploadhere\.com/\w{10}'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """Uploadhere.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("zoidberg", "zoidberg@mujmail.cz")]
