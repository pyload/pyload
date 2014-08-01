# -*- coding: utf-8 -*-
#
# Test links:
# test.bin - 214 B - http://pandapla.net/pew1cz3ot586
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://pandapla.net/tz0rgjfyyoh7

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class PandaPlanet(XFileSharingPro):
    __name__ = "PandaPlanet"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?pandapla\.net/\w{12}'

    __description__ = """Pandapla.net hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"

    HOSTER_NAME = "pandapla.net"

    FILE_SIZE_PATTERN = r'File Size:</b>\s*</td>\s*<td[^>]*>(?P<S>[^<]+)</td>\s*</tr>'
    FILE_NAME_PATTERN = r'File Name:</b>\s*</td>\s*<td[^>]*>(?P<N>[^<]+)</td>\s*</tr>'
    LINK_PATTERN = r'(http://([^/]*?%s|\d+\.\d+\.\d+\.\d+)(:\d+)?(/d/|(?:/files)?/\d+/\w+/)[^"\'<]+\/(?!video\.mp4)[^"\'<]+)' % HOSTER_NAME


getInfo = create_getInfo(PandaPlanet)
