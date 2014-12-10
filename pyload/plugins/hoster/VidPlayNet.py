# -*- coding: utf-8 -*-
#
# Test links:
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://vidplay.net/38lkev0h3jv0

from pyload.plugins.internal.XFSHoster import XFSHoster, create_getInfo


class VidPlayNet(XFSHoster):
    __name    = "VidPlayNet"
    __type    = "hoster"
    __version = "0.04"

    __pattern = r'https?://(?:www\.)?vidplay\.net/\w{12}'

    __description = """VidPlay.net hoster plugin"""
    __license     = "GPLv3"
    __authors     = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


    HOSTER_DOMAIN = "vidplay.net"

    NAME_PATTERN = r'<b>Password:</b></div>\s*<h[1-6]>(?P<N>[^<]+)</h[1-6]>'


getInfo = create_getInfo(VidPlayNet)
