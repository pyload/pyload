# -*- coding: utf-8 -*-

import re

from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class CloudzillaToFolder(SimpleHoster):
    __name__    = "CloudzillaToFolder"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://(?:www\.)?cloudzilla\.to/share/folder/(?P<ID>[\w^_]+)'

    __description__ = """Cloudzilla.to folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


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


getInfo = create_getInfo(CloudzillaToFolder)
