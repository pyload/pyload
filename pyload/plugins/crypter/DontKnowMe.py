# -*- coding: utf-8 -*-

import re

from urllib import unquote

from pyload.plugins.base.Crypter import Crypter


class DontKnowMe(Crypter):
    __name__ = "DontKnowMe"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?dontknow.me/at/\?.+$'

    __description__ = """DontKnow.me decrypter plugin"""
    __authors__ = [("selaux", None)]


    LINK_PATTERN = r'http://dontknow.me/at/\?(.+)$'


    def decrypt(self, pyfile):
        link = re.findall(self.LINK_PATTERN, pyfile.url)[0]
        self.urls = [unquote(link)]
