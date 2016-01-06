# -*- coding: utf-8 -*-

from module.plugins.internal.DeadHoster import DeadHoster


class MegaFilesSe(DeadHoster):
    __name__    = "MegaFilesSe"
    __type__    = "hoster"
    __version__ = "0.06"
    __status__  = "stable"

    __pattern__ = r'http://(?:www\.)?megafiles\.se/\w{12}'
    __config__  = []  #@TODO: Remove in 0.4.10

    __description__ = """MegaFiles.se hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]
