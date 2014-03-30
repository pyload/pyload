# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter


class UlozToFolder(Crypter):
    __name__ = "UlozToFolder"
    __type__ = "crypter"
    __pattern__ = r"http://(?:www\.)?(uloz\.to|ulozto\.(cz|sk|net)|bagruj.cz|zachowajto.pl)/(m|soubory)/.*"
    __version__ = "0.2"
    __description__ = """Uloz.to folder decrypter plugin"""
    __author_name__ = "zoidberg"
    __author_mail__ = "zoidberg@mujmail.cz"

    FOLDER_PATTERN = r'<ul class="profile_files">(.*?)</ul>'
    LINK_PATTERN = r'<br /><a href="/([^"]+)">[^<]+</a>'
    NEXT_PAGE_PATTERN = r'<a class="next " href="/([^"]+)">&nbsp;</a>'

    def decrypt(self, pyfile):
        html = self.load(pyfile.url)

        new_links = []
        for i in xrange(1, 100):
            self.logInfo("Fetching links from page %i" % i)
            found = re.search(self.FOLDER_PATTERN, html, re.DOTALL)
            if found is None:
                self.fail("Parse error (FOLDER)")

            new_links.extend(re.findall(self.LINK_PATTERN, found.group(1)))
            found = re.search(self.NEXT_PAGE_PATTERN, html)
            if found:
                html = self.load("http://ulozto.net/" + found.group(1))
            else:
                break
        else:
            self.logInfo("Limit of 99 pages reached, aborting")

        if new_links:
            self.core.files.addLinks(map(lambda s: "http://ulozto.net/%s" % s, new_links), pyfile.package().id)
        else:
            self.fail('Could not extract any links')
