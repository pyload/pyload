# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.plugins.Crypter import Crypter


class Dereferer(Crypter):
    __name__    = "Dereferer"
    __type__    = "crypter"
    __version__ = "0.10"

    __pattern__ = r'https?://([^/]+)/.*?(?P<url>(ht|f)tps?(://|%3A%2F%2F).*)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Crypter for dereferers"""
    __license__     = "GPLv3"
    __authors__     = [("zoidberg", "zoidberg@mujmail.cz")]


    def decrypt(self, pyfile):
        link = re.match(self.__pattern__, pyfile.url).group('url')
        self.urls = [unquote(link).rstrip('+')]
