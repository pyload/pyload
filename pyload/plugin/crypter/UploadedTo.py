# -*- coding: utf-8 -*-

import re
import urlparse

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class UploadedTo(SimpleCrypter):
    __name    = "UploadedTo"
    __type    = "crypter"
    __version = "0.42"

    __pattern = r'http://(?:www\.)?(uploaded|ul)\.(to|net)/(f|folder|list)/(?P<ID>\w+)'
    __config  = [("use_premium"       , "bool", "Use premium account if available"   , True),
                   ("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """UploadedTo decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("stickell", "l.stickell@yahoo.it")]


    PLAIN_PATTERN = r'<small class="date"><a href="([\w/]+)" onclick='
    NAME_PATTERN = r'<title>(?P<N>.+?)<'


    def getLinks(self):
        m = re.search(self.PLAIN_PATTERN, self.html)
        if m is None:
            self.error(_("PLAIN_PATTERN not found"))

        plain_link = urlparse.urljoin("http://uploaded.net/", m.group(1))
        return self.load(plain_link).split('\n')[:-1]
