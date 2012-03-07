# -*- coding: utf-8 -*-
from module.plugins.hoster.XFileSharingPro import XFileSharingPro, create_getInfo

class FiledinoCom(XFileSharingPro):
    __name__ = "FiledinoCom"
    __type__ = "hoster"
    __pattern__ = r"http://(?:\w*\.)*filedino.com/\w{12}"
    __version__ = "0.01"
    __description__ = """FileDino.com hoster plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    FILE_SIZE_PATTERN = r'File Size : </span><span class="runninggreysmall">(?P<S>.+?)</span>'
    
    HOSTER_NAME = "filedino.com"
    DIRECT_LINK_PATTERN = r'http://www\.filedino\.com/cgi-bin/dl\.cgi/'

getInfo = create_getInfo(FiledinoCom)