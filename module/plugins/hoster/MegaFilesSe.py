# -*- coding: utf-8 -*-

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class MegaFilesSe(XFileSharingPro):
    __name__ = "MegaFilesSe"
    __type__ = "hoster"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?megafiles\.se/\w{12}'

    __description__ = """MegaFiles.se hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"

    HOSTER_NAME = "megafiles.se"

    OFFLINE_PATTERN = r'<b><font[^>]*>File Not Found</font></b><br><br>'
    FILE_NAME_PATTERN = r'<div[^>]+>\s*<b>(?P<N>[^<]+)</b>\s*</div>'


getInfo = create_getInfo(MegaFilesSe)
