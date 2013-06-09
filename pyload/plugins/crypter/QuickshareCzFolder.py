# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class QuickshareCzFolder(Crypter):
    __name__ = "QuickshareCzFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?quickshare.cz/slozka-\d+.*"
    __version__ = "0.1"
    __description__ = """Quickshare.cz Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    
    FOLDER_PATTERN = r'<textarea[^>]*>(.*?)</textarea>'
    LINK_PATTERN = r'(http://www.quickshare.cz/\S+)'

    def decrypt(self, pyfile):
        html = self.load(self.pyfile.url)

        new_links = []      
        found = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if found is None: self.fail("Parse error (FOLDER)")
        new_links.extend(re.findall(self.LINK_PATTERN, found.group(1)))

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')