# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class IcyFilesCom(DeadHoster):
    __name__ = "IcyFilesCom"
    __type__ = "hoster"
    __version__ = "0.06"

    __pattern__ = r'http://(?:www\.)?icyfiles\.com/(.*)'

    __description__ = """IcyFiles.com hoster plugin"""
    __author_name__ = "godofdream"
    __author_mail__ = "soilfiction@gmail.com"


getInfo = create_getInfo(IcyFilesCom)
