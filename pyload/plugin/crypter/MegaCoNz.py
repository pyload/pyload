# -*- coding: utf-8 -*-

import re

from pyload.plugin.Crypter import Crypter


class MegaCoNz(Crypter):
    __name    = "MegaCoNz"
    __type    = "crypter"
    __version = "0.04"

    __pattern = r'(?:https?://(?:www\.)?mega\.co\.nz/|mega:|chrome:.+?)#F!(?P<ID>[\w^_]+)!(?P<KEY>[\w,\\-]+)'
    __config  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description = """Mega.co.nz folder decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("Walter Purcaro", "vuolter@gmail.com")]


    def setup(self):
        self.req.setOption("timeout", 300)


    def decrypt(self, pyfile):
        url       = "https://mega.co.nz/#F!%s!%s" % re.match(self.__pattern, pyfile.url).groups()
        self.html = self.load("http://rapidgen.org/linkfinder", post={'linklisturl': url})
        self.urls = re.findall(r'(https://mega.co.nz/#N!.+?)<', self.html)

        if not self.urls:  #@TODO: Remove in 0.4.10
            self.fail(_("No link grabbed"))
