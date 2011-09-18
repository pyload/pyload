# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class MultiloadCz(Crypter):
    __name__ = "MultiloadCz"
    __type__ = "crypter"
    __pattern__ = r"http://.*multiload.cz/(stahnout|slozka)/.*"
    __version__ = "0.2b"
    __description__ = """multiload.cz"""
    __config__ = [
        ("usedHoster", "str", "Prefered hoster list (bar-separated) ", "rapidshare.com|uloz.to|quickshare.cz")]
    __author_name__ = ("zoidberg")

    # LINK_PATTERN = r'<p class="manager-server"><strong>[^<]*</strong></p><p class="manager-linky"><a href="([^"]+)">'
    FOLDER_PATTERN = r'<form action="" method="get"><textarea[^>]*>([^>]*)</textarea></form>'

    def decrypt(self, pyfile):
        self.html = self.load(self.pyfile.url, decode=True)
        new_links = []

        if re.search(self.__pattern__, self.pyfile.url).group(1) == "slozka":
            found = re.search(self.FOLDER_PATTERN, self.html)
            if found is not None:
                new_links.extend(found.group(1).split())
        else:
            link_pattern = re.compile(r'<p class="manager-server"><strong>('
                                      + self.getConfig("usedHoster")
            + r')</strong></p><p class="manager-linky"><a href="([^"]+)">')

            for found in re.finditer(link_pattern, self.html):
                self.logDebug("ML URL:" + found.group(2))
                new_links.append(found.group(2))

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
            #self.packages.append((self.pyfile.package().name, new_links, self.pyfile.package().name))
        else:
            self.fail('Could not extract any links')
            