# -*- coding: utf-8 -*-

from module.plugins.internal.Crypter import Crypter

import re


class ShSt(Crypter):
    __name__    = "ShSt"
    __type__    = "crypter"
    __version__ = "0.01"

    __pattern__ = r'http://sh\.st/\w+'

    __description__ = """Sh.St decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Frederik Möllers", "fred-public@posteo.de")]


    NAME_PATTERN = r'<title>(?P<N>.+?) - .+</title>'


    def decrypt(self, pyfile):
        package = pyfile.package()
        package_name = package.name
        package_folder = package.folder
        html = self.load("http://deadlockers.com/submit.php", post = { "deadlock" : self.pyfile.url }, decode = True)
        self.packages.append((package_name, [html], package_folder))
