# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.plugin.Crypter import Crypter


class DontKnowMe(Crypter):
    __name    = "DontKnowMe"
    __type    = "crypter"
    __version = "0.10"

    __pattern = r'http://(?:www\.)?dontknow\.me/at/\?.+$'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """DontKnow.me decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("selaux", "")]


    LINK_PATTERN = r'http://dontknow\.me/at/\?(.+)$'


    def decrypt(self, pyfile):
        link = re.findall(self.LINK_PATTERN, pyfile.url)[0]
        self.urls = [unquote(link)]
