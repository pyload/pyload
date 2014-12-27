# -*- coding: utf-8 -*-

from module.plugins.internal.Crypter import Crypter


class MegaCoNzFolder(Crypter):
    __name__    = "MegaCoNzFolder"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'https?://(?:www\.)?mega\.co\.nz/#F![\w+^_]![\w,\\-]+'
    __config__  = [("use_subfolder", "bool", "Save package to subfolder", True),
                   ("subfolder_per_package", "bool", "Create a subfolder for each package", True)]

    __description__ = """Mega.co.nz folder decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Walter Purcaro", "vuolter@gmail.com")]


    def decrypt(self, pyfile):
        self.html = self.load("http://rapidgen.org/linkfinder", post={'linklisturl': self.pyfile.url})
        self.urls = re.findall(r'(https://mega.co.nz/#N!.+?)<', self.html)

        if not self.urls:  #@TODO: Remove in 0.4.10
            self.fail("No link grabbed")
