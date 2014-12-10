# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from pyload.plugins.internal.SimpleCrypter import SimpleCrypter


class UploadedTo(SimpleCrypter):
    __name    = "UploadedTo"
    __type    = "crypter"
    __version = "0.42"

    __pattern = r'http://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/(?P<id>\w+)'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """UploadedTo decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    PLAIN_PATTERN = r'<small class="date"><a href="(?P<plain>[\w/]+)" onclick='
    NAME_PATTERN = r'<title>(?P<N>.+?)<'


    def getLinks(self):
        m = re.search(self.PLAIN_PATTERN, self.html)
        if m is None:
            self.error(_("PLAIN_PATTERN not found"))

        plain_link = urljoin("http://uploaded.net/", m.group('plain'))
        return self.load(plain_link).split('\n')[:-1]
