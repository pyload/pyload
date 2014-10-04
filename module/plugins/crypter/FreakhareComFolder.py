# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FreakhareComFolder(SimpleCrypter):
    __name__ = "FreakhareComFolder"
    __type__ = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://(?:www\.)?freakshare\.com/folder/.+'

    __description__ = """Freakhare.com folder decrypter plugin"""
    __author_name__ = "stickell"
    __author_mail__ = "l.stickell@yahoo.it"

    LINK_PATTERN = r'<a href="(http://freakshare.com/files/[^"]+)" target="_blank">'
    TITLE_PATTERN = r'Folder:</b> (?P<title>.+)'
    PAGES_PATTERN = r'Pages: +(?P<pages>\d+)'


    def loadPage(self, page_n):
        if not hasattr(self, 'f_id') and not hasattr(self, 'f_md5'):
            m = re.search(r'http://freakshare.com/\?x=folder&f_id=(\d+)&f_md5=(\w+)', self.html)
            if m:
                self.f_id = m.group(1)
                self.f_md5 = m.group(2)
        return self.load('http://freakshare.com/', get={'x': 'folder',
                                                        'f_id': self.f_id,
                                                        'f_md5': self.f_md5,
                                                        'entrys': '20',
                                                        'page': page_n - 1,
                                                        'order': ''}, decode=True)
