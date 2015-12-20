# -*- coding: utf-8 -*-

import re

from module.plugins.internal.Crypter import Crypter

class HflixIn(Crypter):
    __name__ = "HflixIn"
    __type__ = "crypter"
    __version__ = "0.1"
    __status__  = "testing"

    __pattern__ = r"http://hflix.in/\w{5}"

    __description__ = """Hflix.in Decrypter Plugin"""
    __license__     = "GPLv3"
    __authors__     = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]


    def decrypt(self, pyfile):
        headers = self.load(pyfile.url, just_header=True)
        if 'refresh' in headers and headers['refresh']:
            m = re.search("\d+;url=(.+)", headers['refresh'])
            if m and "http://hflix.in/admin" not in m.group(1):
                self.packages.append((pyfile.package().name, [m.group(1)], pyfile.package().name))

            else:
                self.offline()
