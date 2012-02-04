# -*- coding: utf-8 -*-

import re 

from module.plugins.Crypter import Crypter

class OronComFolder(Crypter):
    __name__ = "OronComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?oron.com/folder/\w+"
    __version__ = "0.2"
    __description__ = """Oron.com Folder Plugin"""
    __author_name__ = ("DHMH")
    __author_mail__ = ("webmaster@pcProfil.de")

    FOLDER_PATTERN = r'<table width="100%" cellpadding="7" cellspacing="1" class="tbl2">(.*)</table>\n		</div>'
    LINK_PATTERN = r'<a href="([^"]+)" target="_blank">'

    def decryptURL(self, url):
        html = self.load(url)

        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if folder is None: self.fail("Parse error (FOLDER)")
        
        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(0)))
        
        if new_links:
            self.logDebug("Found %d new links" % len(new_links))
            return new_links
        else:
            self.fail('Could not extract any links')
