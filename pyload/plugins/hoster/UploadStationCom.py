# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class UploadStationCom(DeadHoster):
    __name__ = "UploadStationCom"
    __type__ = "hoster"
    __version__ = "0.52"

    __pattern__ = r'http://(?:www\.)?uploadstation\.com/file/(?P<id>[A-Za-z0-9]+)'

    __description__ = """UploadStation.com hoster plugin"""
    __author_name__ = ("fragonib", "zoidberg")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "zoidberg@mujmail.cz")


getInfo = create_getInfo(UploadStationCom)
