# -*- coding: utf-8 -*-
#
# Test links:
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://vidplay.net/38lkev0h3jv0

from pyload.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class VidPlayNet(XFileSharingPro):
    __name__ = "VidPlayNet"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?vidplay\.net/\w{12}'

    __description__ = """VidPlay.net hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"

    HOSTER_NAME = "vidplay.net"

    OFFLINE_PATTERN = r'<b>File Not Found</b><br>\s*<br>'
    FILE_NAME_PATTERN = r'<b>Password:</b></div>\s*<h[1-6]>(?P<N>[^<]+)</h[1-6]>'
    LINK_PATTERN = r'(http://([^/]*?%s|\d+\.\d+\.\d+\.\d+)(:\d+)?(/d/|(?:/files)?/\d+/\w+/)[^"\'<&]+)' % HOSTER_NAME


getInfo = create_getInfo(VidPlayNet)
