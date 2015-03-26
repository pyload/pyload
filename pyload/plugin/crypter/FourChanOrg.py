# -*- coding: utf-8 -*-
#
# Based on 4chandl by Roland Beermann (https://gist.github.com/enkore/3492599)

import re

from pyload.plugin.Crypter import Crypter


class FourChanOrg(Crypter):
    __name    = "FourChanOrg"
    __type    = "crypter"
    __version = "0.31"

    __pattern = r'http://(?:www\.)?boards\.4chan\.org/\w+/res/(\d+)'
    __config  = [("use_subfolder"     , "bool", "Save package to subfolder"          , True),
                   ("subfolder_per_pack", "bool", "Create a subfolder for each package", True)]

    __description = """4chan.org folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = []


    def decrypt(self, pyfile):
        pagehtml = self.load(pyfile.url)
        images = set(re.findall(r'(images\.4chan\.org/[^/]*/src/[^"<]*)', pagehtml))
        self.urls = ["http://" + image for image in images]
