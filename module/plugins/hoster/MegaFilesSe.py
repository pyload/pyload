# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster, create_getInfo


class MegaFilesSe(DeadHoster):
    __name__ = "MegaFilesSe"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?megafiles\.se/\w{12}'

    __description__ = """MegaFiles.se hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"


getInfo = create_getInfo(MegaFilesSe)
