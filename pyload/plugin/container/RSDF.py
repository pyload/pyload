# -*- coding: utf-8 -*-

from __future__ import with_statement

import binascii
import re

import Crypto

from pyload.plugin.Container import Container
from pyload.utils import fs_encode


class RSDF(Container):
    __name    = "RSDF"
    __type    = "container"
    __version = "0.29"

    __pattern = r'.+\.rsdf$'

    __description = """RSDF container decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("spoob", "spoob@pyload.org"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    KEY = "8C35192D964DC3182C6F84F3252239EB4A320D2500000000"
    IV  = "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"


    def decrypt(self, pyfile):
        KEY = binascii.unhexlify(self.KEY)
        IV  = binascii.unhexlify(self.IV)

        iv     = Crypto.Cipher.AES.new(KEY, Crypto.Cipher.AES.MODE_ECB).encrypt(IV)
        cipher = Crypto.Cipher.AES.new(KEY, Crypto.Cipher.AES.MODE_CFB, iv)

        try:
            fs_filename = fs_encode(pyfile.url.strip())
            with open(fs_filename, 'r') as rsdf:
                data = rsdf.read()

        except IOError, e:
            self.fail(e)

        if re.search(r"<title>404 - Not Found</title>", data):
            pyfile.setStatus("offline")

        else:
            try:
                raw_links = binascii.unhexlify(''.join(data.split())).splitlines()

            except TypeError:
                self.fail(_("Container is corrupted"))

            for link in raw_links:
                if not link:
                    continue
                link = cipher.decrypt(link.decode('base64')).replace('CCF: ', '')
                self.urls.append(link)
