# -*- coding: utf-8 -*-

# Test links:
# BigBuckBunny_320x180.mp4 - 61.7 Mb - http://lemuploads.com/uwol0aly9dld

from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo


class LemUploadsCom(XFileSharingPro):
    __name__ = "LemUploadsCom"
    __type__ = "hoster"
    __pattern__ = r'https?://(?:www\.)?lemuploads.com/\w{12}'
    __version__ = "0.01"
    __description__ = """LemUploads.com hoster plugin"""
    __author_name__ = "t4skforce"
    __author_mail__ = "t4skforce1337[AT]gmail[DOT]com"

    HOSTER_NAME = "lemuploads.com"

    FILE_OFFLINE_PATTERN = r'<b>File Not Found</b><br><br>'
    FILE_NAME_PATTERN = r'<b>Password:</b></div>\s*<h2>(?P<N>[^<]+)</h2>'


getInfo = create_getInfo(LemUploadsCom)
