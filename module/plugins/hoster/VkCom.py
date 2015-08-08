# -*- coding: utf-8 -*-
#
# Test links:
#   http://vk.com/video_ext.php?oid=166335015&id=162608895&hash=b55affa83774504b&hd=1

import re

from module.plugins.internal.SimpleHoster import SimpleHoster, create_getInfo


class VkCom(SimpleHoster):
    __name__    = "VkCom"
    __type__    = "hoster"
    __version__ = "0.02"
    __status__  = "testing"

    __pattern__ = r"https?://(?:www\.)?vk\.com/video_ext\.php/\?.+"
    __config__  = [("quality", "Low;High;Auto", "Quality", "Auto")]

    __description__ = """Vk.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    NAME_PATTERN    = r'"md_title":"(?P<N>.+?)"'
    OFFLINE_PATTERN = r'<div id="video_ext_msg">'

    LINK_FREE_PATTERN = r'url\d+":"(.+?)"'


    def handle_free(self, pyfile):
        self.link = re.findall(self.LINK_FREE_PATTERN, self.html)[0 if self.get_config('quality') == "Low" else -1]


getInfo = create_getInfo(VkCom)
