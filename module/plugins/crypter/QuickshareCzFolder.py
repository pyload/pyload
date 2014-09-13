# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class QuickshareCzFolder(Crypter):
    __name__ = "QuickshareCzFolder"
    __type__ = "crypter"
    __version__ = "0.1"

    __pattern__ = r'http://(?:www\.)?quickshare.cz/slozka-\d+.*'

    __description__ = """Quickshare.cz folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FOLDER_PATTERN = r'<textarea[^>]*>(.*?)</textarea>'
    LINK_PATTERN = r'(http://www.quickshare.cz/\S+)'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if m is None:
            self.fail("Parse error (FOLDER)")
        self.urls.extend(re.findall(self.LINK_PATTERN, m.group(1)))

        if not self.urls:
            self.fail('Could not extract any links')
