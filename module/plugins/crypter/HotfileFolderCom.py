# -*- coding: utf-8 -*-

import re

from module.plugins.Crypter import Crypter


class HotfileFolderCom(Crypter):
    __name__ = "HotfileFolderCom"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?hotfile.com/list/\w+/\w+'

    __description__ = """Hotfile.com folder decrypter plugin"""
    __author_name__ = "RaNaN"
    __author_mail__ = "RaNaN@pyload.org"


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        name = re.findall(
            r'<img src="/i/folder.gif" width="23" height="14" style="margin-bottom: -2px;" />([^<]+)', html,
            re.MULTILINE)[0].replace("/", "")
        new_links = re.findall(r'href="(http://(www.)?hotfile\.com/dl/\d+/[0-9a-zA-Z]+[^"]+)', html)

        new_links = [x[0] for x in new_links]

        self.packages = [(name, new_links, name)]
