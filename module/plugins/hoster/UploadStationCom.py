# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class UploadStationCom(DeadHoster):
    __name__    = "UploadStationCom"
    __type__    = "hoster"
    __version__ = "0.52"

    __pattern__ = r'http://(?:www\.)?uploadstation\.com/file/(?P<ID>\w+)'

    __description__ = """UploadStation.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(UploadStationCom)
