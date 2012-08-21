# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class RyushareCom(XFileSharingPro):
    __name__ = "RyushareCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?ryushare.com/\w{12}"
    __version__ = "0.02"
    __description__ = """ryushare.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    HOSTER_NAME = "ryushare.com"
    
    def setup(self):
        self.resumeDownload = self.multiDL = self.premium

getInfo = create_getInfo(RyushareCom)