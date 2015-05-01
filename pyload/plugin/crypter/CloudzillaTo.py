# -*- coding: utf-8 -*-

import re
import urlparse

from pyload.plugin.internal.SimpleCrypter import SimpleCrypter


class CloudzillaTo(SimpleHoster):
    __name    = "CloudzillaTo"
    __type    = "crypter"
    __version = "0.02"

    __pattern = r'http://(?:www\.)?cloudzilla\.to/share/folder/(?P<ID>[\w^_]+)'

    __description = """Cloudzilla.to folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN    = r'<span class="name" title="(?P<N>.+?)"'
    OFFLINE_PATTERN = r'>File not found...<'

    LINK_PATTERN = r'<a href="(.+?)" class="item_href">'

    PASSWORD_PATTERN = r'<div id="pwd_protected">'


    def checkErrors(self):
        m = re.search(self.PASSWORD_PATTERN, self.html)
        if m:
            self.html = self.load(self.pyfile.url, get={'key': self.getPassword()})

        if re.search(self.PASSWORD_PATTERN, self.html):
            self.retry(reason="Wrong password")
