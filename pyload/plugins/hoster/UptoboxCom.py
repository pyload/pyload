# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class UptoboxCom(XFileSharingPro):
    __name__ = "UptoboxCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?uptobox.com/\w{12}"
    __version__ = "0.06"
    __description__ = """Uptobox.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    FILE_INFO_PATTERN = r'<h2>\s*Download File\s*<span[^>]*>(?P<N>[^>]+)</span></h2>\s*[^\(]*\((?P<S>[^\)]+)\)</h2>'
    FILE_OFFLINE_PATTERN = r'<center>File Not Found</center>'
    HOSTER_NAME = "uptobox.com"
   
    def setup(self):
        self.resumeDownload = self.multiDL = self.premium        
        self.chunkLimit = 1

getInfo = create_getInfo(UptoboxCom)