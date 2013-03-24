# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class NovafileCom(XFileSharingPro):
    __name__ = "NovafileCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*novafile\.com/\w{12}"
    __version__ = "0.01"
    __description__ = """novafile.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
       
    FILE_SIZE_PATTERN = r'<div class="size">(?P<S>.+?)</div>'
    #FILE_OFFLINE_PATTERN = '<b>&quot;File Not Found&quot;</b>|File has been removed due to Copyright Claim'
    FORM_PATTERN = r'name="F\d+"'
    ERROR_PATTERN = r'class="alert[^"]*alert-separate"[^>]*>\s*(?:<p>)?(.*?)\s*</'
    DIRECT_LINK_PATTERN = r'<a href="(http://s\d+\.novafile\.com/.*?)" class="btn btn-green">Download File</a>'
    
    HOSTER_NAME = "novafile.com"   
    
    def setup(self):
        self.multiDL = False 

getInfo = create_getInfo(NovafileCom)