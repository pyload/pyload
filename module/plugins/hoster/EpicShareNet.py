# -*- coding: utf-8 -*-
#
# Test links:
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://epicshare.net/fch3m2bk6ihp/BigBuckBunny_320x180.mp4.html

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class EpicShareNet(XFileSharingPro):
    __name__ = "EpicShareNet"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?epicshare\.net/\w{12}'

    __description__ = """EpicShare.net hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"

    HOSTER_NAME = "epicshare.net"

    OFFLINE_PATTERN = r'<b>File Not Found</b><br><br>'
    FILE_NAME_PATTERN = r'<b>Password:</b></div>\s*<h2>(?P<N>[^<]+)</h2>'


getInfo = create_getInfo(EpicShareNet)
