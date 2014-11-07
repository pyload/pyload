# -*- coding: utf-8 -*-

from module.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class MovReelCom(XFSHoster):
    __name__    = "MovReelCom"
    __type__    = "hoster"
    __version__ = "1.24"

    __pattern__ = r'http://(?:www\.)?movreel\.com/\w{12}'

    __description__ = """MovReel.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("JorisV83", "jorisv83-pyload@yahoo.com")]


    HOSTER_DOMAIN = "movreel.com"

    NAME_PATTERN = r'Filename: <b>(?P<N>.+?)<'
    SIZE_PATTERN = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    LINK_PATTERN = r'<a href="([^"]+)">Download Link'


getInfo = create_getInfo(MovReelCom)
