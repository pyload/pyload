# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter, create_getInfo


class CloudzillaToFolder(SimpleHoster):
    __name__    = "CloudzillaTo"
    __type__    = "crypter"
    __version__ = "0.04"
    __status__  = "testing"

    __pattern__ = r'http://(?:www\.)?cloudzilla\.to/share/folder/(?P<ID>[\w^_]+)'
    __config__  = [("activated", "bool", "Activated", True)]

    __description__ = """Cloudzilla.to folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    INFO_PATTERN    = r'<span class="name" title="(?P<N>.+?)"'
    OFFLINE_PATTERN = r'>File not found...<'

    LINK_PATTERN = r'<a href="(.+?)" class="item_href">'

    PASSWORD_PATTERN = r'<div id="pwd_protected">'


    def check_errors(self):
        m = re.search(self.PASSWORD_PATTERN, self.html)
        if m is not None:
            self.html = self.load(self.pyfile.url, get={'key': self.get_password()})

        if re.search(self.PASSWORD_PATTERN, self.html):
            self.retry(msg="Wrong password")


getInfo = create_getInfo(CloudzillaToFolder)
