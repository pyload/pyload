# -*- coding: utf-8 -*-

from __future__ import with_statement

import re
import xml.dom.minidom

from Crypto.Cipher import AES

from module.plugins.Container import Container
from module.utils import decode, fs_encode


class DLC(Container):
    __name__    = "DLC"
    __type__    = "container"
    __version__ = "0.23"

    __pattern__ = r'.+\.dlc$'

    __description__ = """DLC container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
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

        dlckey  = data[-88:]
        dlcdata = data[:-88].decode('base64')

        try:
            rc = re.search(r'<rc>(.+)</rc>', self.load(self.API_URL % dlckey)).group(1).decode('base64')

        except Exception:
            self.fail(_("DLC file is corrupted"))

        dlckey = AES.new(self.KEY, AES.MODE_CBC, self.IV).decrypt(rc)

        self.data     = AES.new(dlckey, AES.MODE_CBC, dlckey).decrypt(dlcdata).decode('base64')
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
