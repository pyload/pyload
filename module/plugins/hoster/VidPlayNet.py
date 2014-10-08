# -*- coding: utf-8 -*-
#
# Test links:
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://vidplay.net/38lkev0h3jv0

from module.plugins.hoster.XFSPHoster import XFSPHoster, create_getInfo


class VidPlayNet(XFSPHoster):
    __name__ = "VidPlayNet"
    __type__ = "hoster"
    __version__ = "0.02"

    __pattern__ = r'https?://(?:www\.)?vidplay\.net/\w{12}'

    __description__ = """VidPlay.net hoster plugin"""
    __authors__ = [("t4skforce", "t4skforce1337[AT]gmail[DOT]com")]


    HOSTER_NAME = "vidplay.net"

    FILE_NAME_PATTERN = r'<b>Password:</b></div>\s*<h[1-6]>(?P<N>[^<]+)</h[1-6]>'
    LINK_PATTERN = r'(http://([^/]*?%s|\d+\.\d+\.\d+\.\d+)(:\d+)?(/d/|(?:/files)?/\d+/\w+/)[^"\'<&]+)' % HOSTER_NAME


getInfo = create_getInfo(VidPlayNet)
