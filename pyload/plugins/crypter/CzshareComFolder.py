# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class CzshareComFolder(Crypter):
    __name__ = "CzshareComFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(\w*\.)*czshare\.(com|cz)/folders/.*"
    __version__ = "0.1"
    __description__ = """Czshare.com Folder Plugin"""
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FOLDER_PATTERN = r'<tr class="subdirectory">\s*<td>\s*<table>(.*?)</table>'
    LINK_PATTERN = r'<td class="col2"><a href="([^"]+)">info</a></td>'
    #NEXT_PAGE_PATTERN = r'<a class="next " href="/([^"]+)">&nbsp;</a>'

    def decrypt(self, pyfile):
        html = self.load(self.pyfile.url)

        new_links = []
        found = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
        if found is None: self.fail("Parse error (FOLDER)")
        new_links.extend(re.findall(self.LINK_PATTERN, found.group(1)))

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')