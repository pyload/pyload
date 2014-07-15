# -*- coding: utf-8 -*-

import re
import urllib

from module.plugins.Crypter import Crypter


class DontKnowMe(Crypter):
    __name__ = "DontKnowMe"
    __version__ = "0.1"
    __type__ = "crypter"

    __pattern__ = r'http://(?:www\.)?dontknow.me/at/\?.+$'

    __description__ = """DontKnow.me decrypter plugin"""
    __author_name__ = "selaux"
    __author_mail__ = None

    LINK_PATTERN = r'http://dontknow.me/at/\?(.+)$'


    def decrypt(self, pyfile):
        link = re.findall(self.LINK_PATTERN, pyfile.url)[0]
        self.urls = [urllib.unquote(link)]
