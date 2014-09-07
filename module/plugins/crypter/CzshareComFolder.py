# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class CzshareComFolder(Crypter):
    __name__ = "CzshareComFolder"
    __type__ = "crypter"
    __version__ = "0.2"

    __pattern__ = r'http://(?:www\.)?(czshare|sdilej)\.(com|cz)/folders/.*'

    __description__ = """Czshare.com folder decrypter plugin, now Sdilej.cz"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FOLDER_PATTERN = r'<tr class="subdirectory">\s*<td>\s*<table>(.*?)</table>'
    LINK_PATTERN = r'<td class="col2"><a href="([^"]+)">info</a></td>'


    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        m = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if m is None:
            self.fail("Parse error (FOLDER)")

        self.urls.extend(re.findall(self.LINK_PATTERN, m.group(1)))
        if not self.urls:
            self.fail('Could not extract any links')
