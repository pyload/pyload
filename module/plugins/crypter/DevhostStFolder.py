# -*- coding: utf-8 -*-
#
# Test links:
# http://d-h.st/users/shine/?fld_id=37263#files

import re

from urlparse import urljoin

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class DevhostStFolder(SimpleCrypter):
    __name__ = "DevhostStFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?d-h\.st/users/\w+/\?fld_id=\d+'

    __description__ = """d-h.st folder decrypter plugin"""
    __author_name_ = "zapp-brannigan"
    __author_mail_ = "fuerst.reinje@web.de"


    LINK_PATTERN = r';"><a href="/(\w+)'


    def getLinks(self):
        return [urljoin("http://d-h.st", link) for link in re.findall(self.LINK_PATTERN, self.html)]
