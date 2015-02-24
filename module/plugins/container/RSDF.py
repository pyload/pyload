# -*- coding: utf-8 -*-

from __future__ import with_statement

import binascii
import re

from Crypto.Cipher import AES

from module.plugins.Container import Container
from module.utils import fs_encode


class RSDF(Container):
    __name__    = "RSDF"
    __type__    = "container"
    __version__ = "0.29"

    __pattern__ = r'.+\.rsdf$'

    __description__ = """RSDF container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("spoob", "spoob@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    KEY = "8C35192D964DC3182C6F84F3252239EB4A320D2500000000"
    IV  = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"


    def decrypt(self, pyfile):
        KEY = binascii.unhexlify(self.KEY)
        IV  = binascii.unhexlify(self.IV)

        iv     = AES.new(KEY, AES.MODE_ECB).encrypt(IV)
        cipher = AES.new(KEY, AES.MODE_CFB, iv)

        try:
            file = fs_encode(pyfile.url.strip())
            with open(file, 'r') as rsdf:
                data = rsdf.read()

        except IOError, e:
            self.fail(e)

        if re.search(r"<title>404 - Not Found</title>", data):
            return

        try:
            for link in binascii.unhexlify(''.join(data.split())).splitlines():
                if not link:
                    continue
                link = cipher.decrypt(link.decode('base64')).replace('CCF: ', '')
                self.urls.append(link)

        except TypeError:
            self.fail(_("Container is corrupted"))
