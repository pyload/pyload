# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter


class FileserveComFolder(Crypter):
    __name__ = "FileserveComFolder"
    __type__ = "crypter"
    __version__ = "0.11"

    __pattern__ = r'http://(?:www\.)?fileserve.com/list/\w+'

    __description__ = """FileServe.com folder decrypter plugin"""
    __author_name__ = "fionnc"
    __author_mail__ = "fionnc@gmail.com"

    FOLDER_PATTERN = r'<table class="file_list">(.*?)</table>'
    LINK_PATTERN = r'<a href="([^"]+)" class="sheet_icon wbold">'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if folder is None:
            self.fail("Parse error (FOLDER)")

        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(1)))

        if new_links:
            self.urls = [map(lambda s: "http://fileserve.com%s" % s, new_links)]
        else:
            self.fail('Could not extract any links')
