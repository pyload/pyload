# -*- coding: utf-8 -*-

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class MovReelCom(XFileSharingPro):
    __name__ = "MovReelCom"
    __type__ = "hoster"
    __version__ = "1.20"

    __pattern__ = r'http://(?:www\.)?movreel.com/.*'

    __description__ = """MovReel.com hoster plugin"""
    __author_name__ = "JorisV83"
    __author_mail__ = "jorisv83-pyload@yahoo.com"

    HOSTER_NAME = "movreel.com"

    FILE_INFO_PATTERN = r'<h3>(?P<N>.+?) <small><sup>(?P<S>[\d.]+) (?P<U>..)</sup> </small></h3>'
    OFFLINE_PATTERN = r'<b>File Not Found</b><br><br>'
    LINK_PATTERN = r'<a href="(http://[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*/.*)">Download Link</a>'


getInfo = create_getInfo(MovReelCom)
