# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class CramitIn(XFileSharingPro):
    __name__ = "CramitIn"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*cramit.in/\w{12}"
    __version__ = "0.03"
    __description__ = """Cramit.in hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    FILE_INFO_PATTERN = r'<span class=t2>\s*(?P<N>.*?)</span>.*?<small>\s*\((?P<S>.*?)\)'
    DIRECT_LINK_PATTERN = r'href="(http://cramit.in/file_download/.*?)"'    
    HOSTER_NAME = "cramit.in"
    
    def setup(self):
        self.multiDL = self.premium

getInfo = create_getInfo(CramitIn)