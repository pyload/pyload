# -*- coding: utf-8 -*-

from ..internal.DeadHoster import DeadHoster


class UploadStationCom(DeadHoster):
    __name__ = "UploadStationCom"
    __type__ = "hoster"
    __version__ = "0.57"
    __status__ = "stable"

    __pattern__ = r'http://(?:www\.)?uploadstation\.com/file/(?P<ID>\w+)'
    __config__ = []  # @TODO: Remove in 0.4.10

    __description__ = """UploadStation.com hoster plugin"""
    __license__ = "GPLv3"
    __authors__ = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                   ("zoidberg", "zoidberg@mujmail.cz")]
