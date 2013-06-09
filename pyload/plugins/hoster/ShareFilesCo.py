# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
import re

class ShareFilesCo(XFileSharingPro):
    __name__ = "ShareFilesCo"
    __type__ = "hoster"
    __pattern__ = r"http://(www\.)?sharefiles\.co/\w{12}"
    __version__ = "0.01"
    __description__ = """Sharefiles.co hoster plugin"""
    __author_name__ = ("stickell")
    __author_mail__ = ("l.stickell@yahoo.it")

    HOSTER_NAME = "sharefiles.co"

    def startDownload(self, link):
        link = link.strip()
        if link.startswith('http://adf.ly'):
            link = re.sub('http://adf.ly/\d+/', '', link)
        if self.captcha: self.correctCaptcha()
        self.logDebug('DIRECT LINK: %s' % link)
        self.download(link)

getInfo = create_getInfo(ShareFilesCo)
