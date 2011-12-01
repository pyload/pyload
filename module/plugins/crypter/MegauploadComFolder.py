# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter
from re import search
from time import time 

class MegauploadComFolder(SimpleCrypter):
    __name__ = "MegauploadComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?megaupload.com/(?:\?f|xml/folderfiles.php\?folderid)=(\w+)"
    __version__ = "0.01"
    __description__ = """Depositfiles.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")
    
    LINK_PATTERN = r'<ROW[^>]*?url="([^"]+)[^>]*?expired="0"></ROW>'
    
    def init (self):
        folderid = search(self.__pattern__, self.pyfile.url).group(1)
        uniq = time() * 1000
        self.url = "http://www.megaupload.com/xml/folderfiles.php?folderid=%s&uniq=%d" % (folderid, uniq)

