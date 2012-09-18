# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class FilesonicComFolder(Crypter):
    __pattern__ = r"http://(\w*\.)?(sharingmatrix|filesonic|wupload)\.[^/]*/folder/\w+/?"
    __version__ = "0.11"
    __description__ = """Filesonic.com/Wupload.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FOLDER_PATTERN = r'<table>\s*<caption>Files Folder</caption>(.*?)</table>'
    LINK_PATTERN = r'<a href="([^"]+)">'

    def decryptURL(self, url):
        html = self.load(url)
        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if not folder: self.fail("Parse error (FOLDER)")

        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(1)))

        if new_links:
            return new_links
        else:
            self.fail('Could not extract any links')

