# -*- coding: utf-8 -*-

from __future__ import with_statement

import re
import xml.dom.minidom

from base64 import standard_b64decode
from Crypto.Cipher import AES

from module.plugins.Container import Container


class DLC(Container):
    __name__        = "DLC"
    __version__     = "0.21"
    __pattern__     = r'.+\.dlc$'

    __description__ = """DLC container decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("RaNaN", "RaNaN@pyload.org"),
                       ("spoob", "spoob@pyload.org"),
                       ("mkaay", "mkaay@mkaay.de"),
                       ("Schnusch", "Schnusch@users.noreply.github.com")]


    def setup(self):
        self.key     = "cb99b5cbc24db398"
        self.iv      = "9bc24cb995cb8db3"
        self.api_url = "http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=pylo&data="


    def decrypt(self, pyfile):
        with open(pyfile.url.replace("\n", "")) as dlc:
            data = dlc.read().strip()

        if not data.endswith("=="):
            data += "=" if data.endswith("=") else "=="

        dlckey  = data[-88:]
        dlcdata = data[:-88]
        dlcdata = standard_b64decode(dlcdata)

        rc = self.req.load(self.api_url + dlckey)
        rc = re.search(r'<rc>(.+)</rc>', rc).group(1)
        rc = standard_b64decode(rc)

        obj    = AES.new(self.key, AES.MODE_CBC, self.iv)
        dlckey = obj.decrypt(rc)
        obj    = AES.new(dlckey, AES.MODE_CBC, dlckey)

        self.data     = standard_b64decode(obj.decrypt(dlcdata))
        self.packages = [(entry[0] if entry[0] else pyfile.name, entry[1], entry[0] if entry[0] else pyfile.name) \
                         for entry in self.getPackages()]


    def getPackages(self):
        root    = xml.dom.minidom.parseString(self.data).documentElement
        content = root.getElementsByTagName("content")[0]
        return self.parsePackages(content)


    def parsePackages(self, startNode):
        return [(standard_b64decode(node.getAttribute("name")).decode("utf8", "replace"), self.parseLinks(node)) \
                for node in startNode.getElementsByTagName("package")]


    def parseLinks(self, startNode):
        return [standard_b64decode(node.getElementsByTagName("url")[0].firstChild.data) \
                for node in startNode.getElementsByTagName("file")]
