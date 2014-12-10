# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.plugins.Crypter import Crypter


class Dereferer(Crypter):
    __name    = "Dereferer"
    __type    = "crypter"
    __version = "0.10"

    __pattern = r'https?://([^/]+)/.*?(?P<url>(ht|f)tps?(://|%3A%2F%2F).*)'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Crypter for dereferers"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    def decrypt(self, pyfile):
        link = re.match(self.__pattern, pyfile.url).group('url')
        self.urls = [unquote(link).rstrip('+')]
