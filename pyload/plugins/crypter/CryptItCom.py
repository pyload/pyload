# -*- coding: utf-8 -*-


import re

from random import randint

from module.plugins.Crypter import Crypter


class CryptItCom(Crypter):
    __name__ = "CryptItCom"
    __type__ = "container"
    __pattern__ = r"http://[\w\.]*?crypt-it\.com/(s|e|d|c)/[\w]+"
    __version__ = "0.1"
    __description__ = """Crypt.It.com Container Plugin"""
    __author_name__ = ("jeix")
    __author_mail__ = ("jeix@hasnomail.de")
        
    def file_exists(self):
        html = self.load(self.pyfile.url)
        if r'<div class="folder">Was ist Crypt-It</div>' in html:
            return False
        return True

    def decrypt(self, pyfile):
        if not self.file_exists():
            self.offline()

        # @TODO parse name and password
        repl_pattern = r"/(s|e|d|c)/"
        url = re.sub(repl_pattern, r"/d/", self.pyfile.url)

        pyfile.name = "tmp_cryptit_%s.ccf" % randint(0,1000)
        location = self.download(url)

        self.packages.append(["Crypt-it Package", [location], "Crypt-it Package"])
        