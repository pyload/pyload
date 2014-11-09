# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class UploadedToFolder(SimpleCrypter):
    __name__    = "UploadedToFolder"
    __type__    = "crypter"
    __version__ = "0.42"

    __pattern__ = r'http://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/(?P<id>\w+)'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """UploadedTo decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    PLAIN_PATTERN = r'<small class="date"><a href="(?P<plain>[\w/]+)" onclick='
    NAME_PATTERN = r'<title>(?P<N>.+?)<'


    def getLinks(self):
        m = re.search(self.PLAIN_PATTERN, self.html)
        if m is None:
            self.error(_("PLAIN_PATTERN not found"))

        plain_link = urljoin("http://uploaded.net/", m.group('plain'))
        return self.load(plain_link).split('\n')[:-1]
