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

    FOLDER_PATTERN = r'<table(?:.*)class="tbl"(?:.*)>(?:.*)<table(?:.*)class="tbl2"(?:.*)>(?P<body>.*)</table>(?:.*)</table>'
    LINK_PATTERN = r'<a href="([^"]+)" target="_blank">'

    def decryptURL(self, url):
        html = self.load(url)

        new_links = []

        if 'No such folder exist' in html:
            # Don't fail because if there's more than a folder for this package
            # and only one of them fails, no urls at all will be added.
            self.logWarning("Folder does not exist")
            return new_links

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if folder is None:
            # Don't fail because if there's more than a folder for this package
            # and only one of them fails, no urls at all will be added.
            self.logWarning("Parse error (FOLDER)")
            return new_links
        
        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(0)))
        
        if new_links:
            self.logDebug("Found %d new links" % len(new_links))
            return new_links
        else:
            # Don't fail because if there's more than a folder for this package
            # and only one of them fails, no urls at all will be added.
            self.logWarning('Could not extract any links')
            return new_links
