# -*- coding: utf-8 -*-

import base64
import binascii
import re

from pyload.plugins.internal.Container import Container
from pyload.utils import fs_encode


class RSDF(Container):
    __name__    = "RSDF"
    __version__ = "0.23"

    __pattern__ = r'.+\.rsdf'

    __description__ = """RSDF container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("spoob", "spoob@pyload.org")]


    def decrypt(self, pyfile):

        from Crypto.Cipher import AES

        infile = fs_encode(pyfile.url.replace("\n", ""))
        Key = binascii.unhexlify('8C35192D964DC3182C6F84F3252239EB4A320D2500000000')

        IV = binascii.unhexlify('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        IV_Cipher = AES.new(Key, AES.MODE_ECB)
        IV = IV_Cipher.encrypt(IV)

        obj = AES.new(Key, AES.MODE_CFB, IV)

        try:
            with open(infile, 'r') as rsdf:
                data = rsdf.read()
        except IOError, e:
            self.fail(str(e))

        if re.search(r"<title>404 - Not Found</title>", data) is None:
            data = binascii.unhexlify(''.join(data.split()))
            data = data.splitlines()

            for link in data:
                if not link:
                    continue
                link = base64.b64decode(link)
                link = obj.decrypt(link)
                decryptedUrl = link.replace('CCF: ', '')
                self.urls.append(decryptedUrl)

            self.logDebug("Adding package %s with %d links" % (pyfile.package().name, len(self.urls)))
