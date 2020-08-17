# -*- coding: utf-8 -*-

#
# Test links:
#   http://vk.com/video_ext.php?oid=166335015&id=162608895&hash=b55affa83774504b&hd=1

import re

from ..base.simple_downloader import SimpleDownloader


class VkCom(SimpleDownloader):
    __name__ = "VkCom"
    __type__ = "downloader"
    __version__ = "0.06"
    __status__ = "testing"

    __pattern__ = r"https?://(?:www\.)?vk\.com/video_ext\.php/\?.+"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        ("fallback", "bool", "Fallback to free download if premium fails", True),
        ("chk_filesize", "bool", "Check file size", True),
        ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10),
    ]

    __description__ = """Vk.com downloader plugin"""
    __license__ = "GPLv3"
    __authors__ = [("Walter Purcaro", "vuolter@gmail.com")]

    NAME_PATTERN = r'"md_title":"(?P<N>.+?)"'
    OFFLINE_PATTERN = r'<div id="video_ext_msg">'

    LINK_FREE_PATTERN = r'url\d+":"(.+?)"'

    def handle_free(self, pyfile):
        self.link = re.findall(self.LINK_FREE_PATTERN, self.data)[
            0 if self.config.get("quality") == "Low" else -1
        ]
