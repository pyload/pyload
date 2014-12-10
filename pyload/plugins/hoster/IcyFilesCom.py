# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class IcyFilesCom(DeadHoster):
    __name    = "IcyFilesCom"
    __type    = "hoster"
    __version = "0.06"

    __pattern = r'http://(?:www\.)?icyfiles\.com/(.*)'

    __description = """IcyFiles.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("godofdream", "soilfiction@gmail.com")]


getInfo = create_getInfo(IcyFilesCom)
