# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
import re

class StreamcloudEu(XFileSharingPro):
    __name__ = "StreamcloudEu"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?streamcloud\.eu/\S+"
    __version__ = "0.01"
    __description__ = """Streamcloud.eu hoster plugin"""
    __author_name__ = ("seoester")
    __author_mail__ = ("seoester@googlemail.com")

    HOSTER_NAME = "streamcloud.eu"
    DIRECT_LINK_PATTERN = r'file: "(http://(stor|cdn)\d+\.streamcloud.eu:?\d*/.*/video\.mp4)",'

    def setup(self):
        XFileSharingPro.setup(self)
        self.multiDL = True

    def getDownloadLink(self):
        found = re.search(self.DIRECT_LINK_PATTERN, self.html, re.S)
        if found:
            return found.group(1)

        return XFileSharingPro.getDownloadLink(self)

getInfo = create_getInfo(StreamcloudEu)
