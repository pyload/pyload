# -*- coding: utf-8 -*-

import re
from pyload.plugins.Crypter import Crypter


class LetitbitNet(Crypter):
    __name    = "LetitbitNet"
    __type    = "crypter"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?letitbit\.net/folder/\w+'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Letitbit.net folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("DHMH", "webmaster@pcProfil.de"),
                       ("z00nx", "z00nx0@gmail.com")]


    FOLDER_PATTERN = r'<table>(.*)</table>'
    LINK_PATTERN = r'<a href="([^"]+)" target="_blank">'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        folder = re.search(self.FOLDER_PATTERN, html, re.S)
        if folder is None:
            self.error(_("FOLDER_PATTERN not found"))

        self.urls.extend(re.findall(self.LINK_PATTERN, folder.group(0)))
