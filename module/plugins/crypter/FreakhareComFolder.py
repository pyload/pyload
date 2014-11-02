# -*- coding: utf-8 -*-

import re

from module.plugins.internal.SimpleCrypter import SimpleCrypter


class FreakhareComFolder(SimpleCrypter):
    __name__    = "FreakhareComFolder"
    __type__    = "crypter"
    __version__ = "0.03"

    __pattern__ = r'http://(?:www\.)?freakshare\.com/folder/.+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Freakhare.com folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("stickell", "l.stickell@yahoo.it")]


    LINK_PATTERN = r'<a href="(http://freakshare\.com/files/[^"]+)" target="_blank">'
    NAME_PATTERN = r'Folder:</b> (.+)'
    PAGES_PATTERN = r'Pages: +(\d+)'


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
