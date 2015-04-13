# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster


class MovReelCom(XFSHoster):
    __name__    = "MovReelCom"
    __type__    = "hoster"
    __version__ = "1.24"

    __pattern__ = r'http://(?:www\.)?movreel\.com/\w{12}'

    __description__ = """MovReel.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("JorisV83", "jorisv83-pyload@yahoo.com")]


    LINK_PATTERN = r'<a href="(.+?)">Download Link'

