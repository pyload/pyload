# -*- coding: utf-8 -*-

import re

from pyload.plugin.Crypter import Crypter


class FileserveCom(Crypter):
    __name    = "FileserveCom"
    __type    = "crypter"
    __version = "0.11"

    __pattern = r'http://(?:www\.)?fileserve\.com/list/\w+'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """FileServe.com folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("fionnc", "fionnc@gmail.com")]


    FOLDER_PATTERN = r'<table class="file_list">(.*?)</table>'
    LINK_PATTERN = r'<a href="(.+?)" class="sheet_icon wbold">'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        new_links = []

        folder = re.search(self.FOLDER_PATTERN, html, re.S)
        if folder is None:
            self.error(_("FOLDER_PATTERN not found"))

        new_links.extend(re.findall(self.LINK_PATTERN, folder.group(1)))

        if new_links:
            self.urls = [map(lambda s: "http://fileserve.com%s" % s, new_links)]
