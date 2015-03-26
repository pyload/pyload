# -*- coding: utf-8 -*-

import re
from pyload.plugin.Crypter import Crypter


class MultiloadCz(Crypter):
    __name    = "MultiloadCz"
    __type    = "crypter"
    __version = "0.40"

    __pattern = r'http://(?:[^/]*\.)?multiload\.cz/(stahnout|slozka)/.+'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"           , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package" , True),
                   ("usedHoster"        , "str" , "Prefered hoster list (bar-separated)", ""  ),
                   ("ignoredHoster"     , "str" , "Ignored hoster list (bar-separated)" , ""  )]

    __description = """Multiload.cz decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("zoidberg", "zoidberg@mujmail.cz")]


    FOLDER_PATTERN = r'<form action="" method="get"><textarea[^>]*>([^>]*)</textarea></form>'
    LINK_PATTERN = r'<p class="manager-server"><strong>([^<]+)</strong></p><p class="manager-linky"><a href="([^"]+)">'


    def decrypt(self, pyfile):
        self.html = self.load(pyfile.url, decode=True)

        if re.match(self.__pattern, pyfile.url).group(1) == "slozka":
            m = re.search(self.FOLDER_PATTERN, self.html)
            if m:
                self.urls.extend(m.group(1).split())
        else:
            m = re.findall(self.LINK_PATTERN, self.html)
            if m:
                prefered_set = set(self.getConfig('usedHoster').split('|'))
                self.urls.extend(x[1] for x in m if x[0] in prefered_set)

                if not self.urls:
                    ignored_set = set(self.getConfig('ignoredHoster').split('|'))
                    self.urls.extend(x[1] for x in m if x[0] not in ignored_set)
