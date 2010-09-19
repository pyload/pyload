#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter

class NetfolderIn(Crypter):
    __name__ = "NetfolderIn"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?netfolder.in/(\w+/\w+|folder.php)"
    __version__ = "0.1"
    __description__ = """NetFolder Download Plugin"""
    __author_name__ = ("RaNaN")
    __author_mail__ = ("RaNaN@pyload.org")

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        name = re.findall(r'<span style="color: #ff9000;">([^<]+)', html)[0]
        new_links = re.findall(r'href="(http://.{0,3}netload\.in/(datei|index.php?id=10&file_id=)[^"]+)', html)

        new_links = [x[0] for x in new_links]

        self.packages.append((name, new_links, name))