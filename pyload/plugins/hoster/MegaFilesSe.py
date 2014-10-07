# -*- coding: utf-8 -*-

from pyload.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class MegaFilesSe(DeadHoster):
    __name__ = "MegaFilesSe"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?megafiles\.se/\w{12}'

    __description__ = """MegaFiles.se hoster plugin"""
    __authors__ = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


getInfo = create_getInfo(MegaFilesSe)
