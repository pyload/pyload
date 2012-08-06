# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class DdlstorageCom(XFileSharingPro):
    __name__ = "DdlstorageCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*?ddlstorage.com/\w{12}(/?\w*)"
    __version__ = "0.02"
    __description__ = """DDLStorage.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    def setup(self):
        self.resumeDownload = self.multiDL = self.premium

getInfo = create_getInfo(DdlstorageCom)
