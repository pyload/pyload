# -*- coding: utf-8 -*-

from pyload.plugin.internal.DeadHoster import DeadHoster


class UploadStationCom(DeadHoster):
    __name__    = "UploadStationCom"
    __type__    = "hoster"
    __version__ = "0.52"

    __pattern__ = r'http://(?:www\.)?uploadstation\.com/file/(?P<ID>\w+)'
    __config__  = []

    __description__ = """UploadStation.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("zoidberg", "zoidberg@mujmail.cz")]
