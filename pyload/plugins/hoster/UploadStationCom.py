# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class UploadStationCom(DeadHoster):
    __name    = "UploadStationCom"
    __type    = "hoster"
    __version = "0.52"

    __pattern = r'http://(?:www\.)?uploadstation\.com/file/(?P<id>\w+)'

    __description = """UploadStation.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("fragonib", "fragonib[AT]yahoo[DOT]es"),
                       ("zoidberg", "zoidberg@mujmail.cz")]


getInfo = create_getInfo(UploadStationCom)
