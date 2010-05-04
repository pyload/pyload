#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import binascii

from module.plugins.Plugin import Plugin

class RSDF(Plugin):

    def __init__(self, parent):
        Plugin.__init__(self, parent)
        props = {}
        props['name'] = "RSDF"
        props['type'] = "container"
        props['pattern'] = r"(?!http://).*\.rsdf"
        props['version'] = "0.2"
        props['description'] = """RSDF Container Decode Plugin"""
        props['author_name'] = ("RaNaN", "spoob")
        props['author_mail'] = ("RaNaN@pyload.org", "spoob@pyload.org")
        self.props = props
        self.parent = parent
        self.multi_dl = True
        self.links = []

    def proceed(self, url, location):
        from Crypto.Cipher import AES

        infile = url.replace("\n", "")
        Key = binascii.unhexlify('8C35192D964DC3182C6F84F3252239EB4A320D2500000000')

        IV = binascii.unhexlify('FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF')
        IV_Cipher = AES.new(Key, AES.MODE_ECB)
        IV = IV_Cipher.encrypt(IV)

        obj = AES.new(Key, AES.MODE_CFB, IV)

        rsdf = open(infile, 'r')

        data = rsdf.read()
        data = binascii.unhexlify(''.join(data.split()))
        data = data.splitlines()

        for link in data:
            link = base64.b64decode(link)
            link = obj.decrypt(link)
            decryptedUrl = link.replace('CCF: ', '')
            self.links.append(decryptedUrl)

        rsdf.close()
