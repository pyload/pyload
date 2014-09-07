# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.plugins.Crypter import Crypter


class Dereferer(Crypter):
    __name__ = "Dereferer"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = r'https?://([^/]+)/.*?(?P<url>(ht|f)tps?(://|%3A%2F%2F).*)'

    __description__ = """Crypter for dereferers"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"


    def decrypt(self, pyfile):
        link = re.match(self.__pattern__, pyfile.url).group('url')
        self.urls = [unquote(link).rstrip('+')]
