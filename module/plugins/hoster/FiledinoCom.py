# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo
import re

class FiledinoCom(XFileSharingPro):
    __name__ = "FiledinoCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*(file(dino|fat).com)/\w{12}"
    __version__ = "0.02"
    __description__ = """FileDino / FileFat hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    FILE_SIZE_PATTERN = r'File Size : </(span|font)><(span|font)[^>]*>(?P<S>.+?)</(span|font)>'
    DIRECT_LINK_PATTERN = r'http://www\.file(dino|fat)\.com/cgi-bin/dl\.cgi/'
    
    def setup(self):
        self.HOSTER_NAME = re.search(self.__pattern__, self.pyfile.url).group(1)
        self.multiDL = False 

getInfo = create_getInfo(FiledinoCom)