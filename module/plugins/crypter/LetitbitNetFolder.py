# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class LetitbitNetFolder(Crypter):
    __name__ = "LetitbitNetFolder"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?letitbit.net/folder/\w+'

    __description__ = """Letitbit.net folder decrypter plugin"""
    __author_name__ = ("DHMH", "z00nx")
    __author_mail__ = ("webmaster@pcProfil.de", "z00nx0@gmail.com")

    FOLDER_PATTERN = r'<table>(.*)</table>'
    LINK_PATTERN = r'<a href="([^"]+)" target="_blank">'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        folder = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if folder is None:
            self.fail("Parse error (FOLDER)")

        self.urls.extend(re.findall(self.LINK_PATTERN, folder.group(0)))

        if not self.urls:
            self.fail('Could not extract any links')
