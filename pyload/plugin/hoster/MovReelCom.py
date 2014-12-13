# -*- coding: utf-8 -*-

from pyload.plugin.internal.XFSHoster import XFSHoster, create_getInfo


class MovReelCom(XFSHoster):
    __name    = "MovReelCom"
    __type    = "hoster"
    __version = "1.24"

    __pattern = r'http://(?:www\.)?movreel\.com/\w{12}'

    __description = """MovReel.com hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("JorisV83", "jorisv83-pyload@yahoo.com")]


    HOSTER_DOMAIN = "movreel.com"

    NAME_PATTERN = r'Filename: <b>(?P<N>.+?)<'
    SIZE_PATTERN = r'Size: (?P<S>[\d.,]+) (?P<U>[\w^_]+)'

    LINK_PATTERN = r'<a href="([^"]+)">Download Link'


getInfo = create_getInfo(MovReelCom)
