# -*- coding: utf-8 -*-

from module.plugins.Crypter import Crypter, Package
import re

class XfilesharingProFolder(Crypter):
    __name__ = "XfilesharingProFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?((easybytez|turboupload|uploadville|file4safe|fileband|filebeep|grupload|247upload)\.com|(muchshare|annonhost).net|bzlink.us)/users/.*"  
    __version__ = "0.01"
    __description__ = """Generic XfilesharingPro Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    LINK_PATTERN = r'<div class="link"><a href="([^"]+)" target="_blank">[^<]*</a></div>'
    SUBFOLDER_PATTERN = r'<TD width="1%"><img src="[^"]*/images/folder2.gif"></TD><TD><a href="([^"]+)"><b>(?!\. \.<)([^<]+)</b></a></TD>' 
  
    def decryptURL(self, url):
        return self.decryptFile(self.load(url, decode = True))

    def decryptFile(self, html):
        new_links = []

        new_links.extend(re.findall(self.LINK_PATTERN, html))
        
        subfolders = re.findall(self.SUBFOLDER_PATTERN, html)
        #self.logDebug(subfolders)        
        for (url, name) in subfolders:
            if self.package: name = "%s/%s" % (self.package.name, name)                 
            new_links.append(Package(name, [url]))        
           
        if not new_links: self.fail('Could not extract any links')
    
        return new_links