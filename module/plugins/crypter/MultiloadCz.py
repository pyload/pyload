# -*- coding: utf-8 -*-

import re
from module.plugins.Crypter import Crypter

class MultiloadCz(Crypter):
    __name__ = "MultiloadCz"
    __type__ = "crypter"
    __pattern__ = r"http://.*multiload.cz/(stahnout|slozka)/.*"
    __version__ = "0.4"
    __description__ = """multiload.cz"""
    __config__ = [("usedHoster", "str", "Prefered hoster list (bar-separated) ", ""),
        ("ignoredHoster", "str", "Ignored hoster list (bar-separated) ", "")]
    __author_name__ = ("zoidberg")
    __author_mail__ = ("zoidberg@mujmail.cz")

    FOLDER_PATTERN = r'<form action="" method="get"><textarea[^>]*>([^>]*)</textarea></form>'
    LINK_PATTERN = r'<p class="manager-server"><strong>([^<]+)</strong></p><p class="manager-linky"><a href="([^"]+)">'

    def decrypt(self, pyfile):
        self.html = self.load(self.pyfile.url, decode=True)
        new_links = []

        if re.search(self.__pattern__, self.pyfile.url).group(1) == "slozka":
            found = re.search(self.FOLDER_PATTERN, self.html)
            if found is not None:
                new_links.extend(found.group(1).split())
        else:
            found = re.findall(self.LINK_PATTERN, self.html)
            if found:
                prefered_set = set(self.getConfig("usedHoster").split('|'))
                new_links.extend([x[1] for x in found if x[0] in prefered_set])

                if not new_links:
                    ignored_set = set(self.getConfig("ignoredHoster").split('|'))
                    new_links.extend([x[1] for x in found if x[0] not in ignored_set])

        if new_links:
            self.core.files.addLinks(new_links, self.pyfile.package().id)
        else:
            self.fail('Could not extract any links')