# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class FilerioCom(XFileSharingPro):
    __name__ = "FilerioCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*file(rio|keen).com/\w{12}"
    __version__ = "0.01"
    __description__ = """FileRio.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
       
    FILE_OFFLINE_PATTERN = '<b>&quot;File Not Found&quot;</b>|File has been removed due to Copyright Claim'
    HOSTER_NAME = "filerio.com"
    DIRECT_LINK_PATTERN = r'Download Link:.*?<a href="(.*?)"'
    
    def setup(self):
        self.multiDL = False 

getInfo = create_getInfo(FilerioCom)