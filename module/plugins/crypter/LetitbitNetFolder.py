# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class LetitbitNetFolder(Crypter):
    __name__ = "LetitbitNetFolder"
    __version__ = "0.1"
    __type__ = "crypter"

    __pattern__ = r'http://(?:www\.)?letitbit.net/folder/\w+'

    __description__ = """Letitbit.net folder decrypter plugin"""
    __author_name__ = ("DHMH", "z00nx")
    __author_mail__ = ("webmaster@pcProfil.de", "z00nx0@gmail.com")

    FOLDER_PATTERN = r'<table>(.*)</table>'
    LINK_PATTERN = r'<a href="([^"]+)" target="_blank">'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if not folder:
            self.fail("Parse error (FOLDER)")

        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(0)))

        if new_links:
            self.core.files.addLinks(new_links, pyfile.package().id)
        else:
            self.fail('Could not extract any links')
