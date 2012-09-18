# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class DdlstorageCom(XFileSharingPro):
    __name__ = "DdlstorageCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?ddlstorage.com/\w{12}"
    __version__ = "0.06"
    __description__ = """DDLStorage.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    FILE_INFO_PATTERN = r'<h2>\s*Download File\s*<span[^>]*>(?P<N>[^>]+)</span></h2>\s*[^\(]*\((?P<S>[^\)]+)\)</h2>'
    HOSTER_NAME = "ddlstorage.com"
   
    def setup(self):
        self.resumeDownload = self.multiDL = self.premium        
        self.chunkLimit = 1

getInfo = create_getInfo(DdlstorageCom)