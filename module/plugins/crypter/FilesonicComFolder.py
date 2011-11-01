# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class FilesonicComFolder(Crypter):
    __name__ = "FilesonicComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(\w*\.)?(sharingmatrix|filesonic|wupload)\.[^/]*/folder/\d+/?"
    __version__ = "0.10"
    __description__ = """Filesonic.com/Wupload.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FOLDER_PATTERN = r'<table>\s*<caption>Files Folder</caption>(.*?)</table>'
    LINK_PATTERN = r'<a href="([^"]+)">'

    def decrypt(self, pyfile):
        html = self.load(self.pyfile.url)

        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if not folder: self.fail("Parse error (FOLDER)")

        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(1)))

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')