# -*- coding: utf-8 -*-

import re
from module.plugins.internal.Crypter import Crypter


class LetitbitNetFolder(Crypter):
    __name__    = "LetitbitNetFolder"
    __type__    = "crypter"
    __version__ = "0.12"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?letitbit\.net/folder/\w+'
    __config__  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description__ = """Letitbit.net folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("DHMH", "webmaster@pcProfil.de"),
                       ("z00nx", "z00nx0@gmail.com")]


    FOLDER_PATTERN = r'<table>(.*)</table>'
    LINK_PATTERN = r'<a href="(.+?)" target="_blank">'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        folder = re.search(self.FOLDER_PATTERN, html, re.S)
        if folder is None:
            self.error(_("FOLDER_PATTERN not found"))

        self.urls.extend(re.findall(self.LINK_PATTERN, folder.group(0)))
