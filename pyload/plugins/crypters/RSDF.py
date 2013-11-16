#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import binascii
import re

from module.plugins.Crypter import Crypter

class RSDF(Crypter):
    __name__ = "RSDF"
    __version__ = "0.21"
    __pattern__ = r".*\.rsdf"
    __description__ = """RSDF Container Decode Plugin"""
    __author_name__ = ("RaNaN", "spoob")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org")

    
    def decrypt(self, pyfile):
    
        from Crypto.Cipher import AES

        infile = pyfile.url.replace("\n", "")
        Key = binascii.unhexlify('8C35192D964DC3182C6F84F3252239EB4A320D2500000000')

        IV = binascii.unhexlify('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        IV_Cipher = AES.new(Key, AES.MODE_ECB)
        IV = IV_Cipher.encrypt(IV)

        obj = AES.new(Key, AES.MODE_CFB, IV)

        rsdf = open(infile, 'r')

        data = rsdf.read()
        rsdf.close()

        if re.search(r"<title>404 - Not Found</title>", data) is None:
            data = binascii.unhexlify(''.join(data.split()))
            data = data.splitlines()

            links = []
            for link in data:
                link = base64.b64decode(link)
                link = obj.decrypt(link)
                decryptedUrl = link.replace('CCF: ', '')
                links.append(decryptedUrl)

            self.log.debug("%s: adding package %s with %d links" % (self.__name__,pyfile.package().name,len(links)))
            self.packages.append((pyfile.package().name, links))        
