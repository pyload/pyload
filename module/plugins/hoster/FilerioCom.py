# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class FilerioCom(XFileSharingPro):
    __name__ = "FilerioCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(filerio\.(in|com)|filekeen\.com)/\w{12}"
    __version__ = "0.02"                             
    __description__ = """FileRio.in hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
       
    FILE_OFFLINE_PATTERN = '<b>&quot;File Not Found&quot;</b>|File has been removed due to Copyright Claim'
    HOSTER_NAME = "filerio.in"
    FILE_URL_REPLACEMENTS = [(r'http://.*?/','http://filerio.in/')]
    
    def setup(self):
        self.resumeDownload = self.multiDL = self.premium 

getInfo = create_getInfo(FilerioCom)