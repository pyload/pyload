# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class UploadStationCom(DeadHoster):
    __name__ = "UploadStationCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:www\.)?uploadstation\.com/file/(?P<id>[A-Za-z0-9]+)"
    __version__ = "0.52"
    __description__ = """UploadStation.Com File Download Hoster"""
    __author_name__ = ("fragonib", "zoidberg")
    __author_mail__ = ("fragonib[AT]yahoo[DOT]es", "zoidberg@mujmail.cz")


getInfo = create_getInfo(UploadStationCom)
