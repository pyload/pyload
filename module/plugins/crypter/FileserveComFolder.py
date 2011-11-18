# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class FileserveComFolder(Crypter):
    __name__ = "FileserveComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(www\.)?fileserve\.com/list/\w+"
    __version__ = "0.10"
    __description__ = """Fileserve.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FOLDER_PATTERN = r'<div class="middle">(.*?)<div class="tail">'
    LINK_PATTERN = r'<a href="(/file/[^"]+)"'

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if not folder: self.fail("Parse error (FOLDER)")

        new_links.extend(map(lambda s:"http://www.fileserve.com%s" % s, re.findall(self.LINK_PATTERN, folder.group(1))))

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')