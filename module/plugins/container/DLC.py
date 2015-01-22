# -*- coding: utf-8 -*-

import base64
import re

from Crypto.Cipher import AES
from xml.dom.minidom import parseString

from module.plugins.Container import Container


class DLC(Container):
    __name__        = "DLC"
    __pattern__     = r'.*\.dlc$'
    __version__     = "0.2"
    __description__ = """DLC Container Decode Plugin"""
    __author_name__ = ("RaNaN", "spoob", "mkaay", "Schnusch")
    __author_mail__ = ("RaNaN@pyload.org", "spoob@pyload.org", "mkaay@mkaay.de", "Schnusch@users.noreply.github.com")

    key = "cb99b5cbc24db398"
    iv  = "9bc24cb995cb8db3"
    dlc_api_url = "http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=pylo&data="

    def decrypt(self, pyfile):
        infile = pyfile.url.replace("\n", "")

        dlc = open(infile, "r")
        data = dlc.read().strip()
        dlc.close()
        if not data.endswith("=="):
            if data.endswith("="):
                data += "="
            else:
                data += "=="
        dlckey = data[-88:]
        dlcdata = data[:-88]
        dlcdata = base64.standard_b64decode(dlcdata)
        rc = self.req.load(self.dlc_api_url + dlckey)
        rc = re.search(r'<rc>(.+)</rc>', rc).group(1)
        rc = base64.standard_b64decode(rc)
        obj = AES.new(self.key, AES.MODE_CBC, self.iv)
        dlckey = obj.decrypt(rc)
        obj = AES.new(dlckey, AES.MODE_CBC, dlckey)
        self.data = base64.standard_b64decode(obj.decrypt(dlcdata))
        for entry in self.getPackages():
            self.packages.append((entry[0] if entry[0] else pyfile.name, entry[1], entry[0] if entry[0] else pyfile.name))

    def createNewPackage(self):
        return True

    def getPackages(self):
        xml = parseString(self.data)
        root = xml.documentElement
        contentNode = root.getElementsByTagName("content")[0]
        return self.parsePackages(contentNode)

    def parsePackages(self, startNode):
        c = []
        for node in startNode.getElementsByTagName("package"):
            c.append((base64.standard_b64decode(node.getAttribute("name")).decode("utf8", "replace"), self.parseLinks(node)))

        return c

    def parseLinks(self, startNode):
        c = []
        for node in startNode.getElementsByTagName("file"):
            c.append(base64.standard_b64decode(node.getElementsByTagName("url")[0].firstChild.data))

        return c
