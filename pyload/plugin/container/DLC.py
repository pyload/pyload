# -*- coding: utf-8 -*-

from __future__ import with_statement

import re
import xml.dom.minidom

from Crypto.Cipher import AES

from pyload.plugin.Container import Container
from pyload.utils import decode, fs_encode


class DLC(Container):
    __name    = "DLC"
    __type    = "container"
    __version = "0.24"

    __pattern = r'.+\.dlc$'

    __description = """DLC container decrypter plugin"""
    __license     = "GPLv3"
    __authors     = [("RaNaN", "RaNaN@pyload.org"),
                       ("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("Schnusch", "Schnusch@users.noreply.github.com"),
                       ("Walter Purcaro", "vuolter@gmail.com")]


    KEY     = "cb99b5cbc24db398"
    IV      = "9bc24cb995cb8db3"
    API_URL = "http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=pylo&data=%s"


    def decrypt(self, pyfile):
        file = fs_encode(pyfile.url.strip())
        with open(file) as dlc:
            data = dlc.read().strip()

        data += '=' * (-len(data) % 4)

        dlc_key     = data[-88:]
        dlc_data    = data[:-88].decode('base64')
        dlc_content = self.load(self.API_URL % dlc_key)

        try:
            rc = re.search(r'<rc>(.+)</rc>', dlc_content, re.S).group(1).decode('base64')

        except AttributeError:
            self.fail(_("Container is corrupted"))

        cipher = AES.new(self.KEY, AES.MODE_CBC, self.IV).decrypt(rc)

        self.data     = AES.new(cipher, AES.MODE_CBC, cipher).decrypt(dlc_data).decode('base64')
        self.packages = [(entry[0] if entry[0] else pyfile.name, entry[1], entry[0] if entry[0] else pyfile.name) \
                         for entry in self.getPackages()]


    def getPackages(self):
        root    = xml.dom.minidom.parseString(self.data).documentElement
        content = root.getElementsByTagName("content")[0]
        return self.parsePackages(content)


    def parsePackages(self, startNode):
        return [(decode(node.getAttribute("name")).decode('base64'), self.parseLinks(node)) \
                for node in startNode.getElementsByTagName("package")]


    def parseLinks(self, startNode):
        return [node.getElementsByTagName("url")[0].firstChild.data.decode('base64') \
                for node in startNode.getElementsByTagName("file")]
