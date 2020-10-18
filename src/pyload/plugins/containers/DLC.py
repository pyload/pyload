# -*- coding: utf-8 -*-

import base64
import os
import re
import xml.dom.minidom

import Crypto.Cipher.AES

from pyload.core.utils.old import decode

from ..base.container import BaseContainer

class BadDLC(Exception):
    pass


class DLCDecrypter(object):
    KEY = "cb99b5cbc24db398"
    IV = "9bc24cb995cb8db3"
    API_URL = "http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=pylo&data=%s"

    def __init__(self, plugin):
        self.plugin = plugin

    def decrypt(self, data):
        data = data.strip()

        data += '=' * (-len(data) % 4)

        dlc_key = data[-88:]
        dlc_data =  base64.b64decode(data[:-88])
        dlc_content = self.plugin.load(self.API_URL % dlc_key)

        try:
            rc =  base64.b64decode(re.search(r'<rc>(.+)</rc>', dlc_content, re.S).group(1))[:16]

        except AttributeError:
            raise BadDLC

        key = iv = Crypto.Cipher.AES.new(self.KEY, Crypto.Cipher.AES.MODE_CBC, self.IV).decrypt(rc)

        xml_data =  base64.b64decode(Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv).decrypt(dlc_data))

        root = xml.dom.minidom.parseString(xml_data).documentElement
        content_node = root.getElementsByTagName("content")[0]

        packages = DLCDecrypter._parse_packages(content_node)

        return packages

    @staticmethod
    def _parse_packages(start_node):
        return [
            (
                base64.b64decode(decode(node.getAttribute("name"))).decode('utf-8'),
                DLCDecrypter._parse_links(node)
            )
            for node in start_node.getElementsByTagName("package")
        ]

    @staticmethod
    def _parse_links(start_node):
        return [
            base64.b64decode(node.getElementsByTagName("url")[0].firstChild.data).decode('utf-8')
            for node in start_node.getElementsByTagName("file")
        ]


class DLC(BaseContainer):
    __name__ = "DLC"
    __type__ = "container"
    __version__ = "0.34"
    __status__ = "testing"

    __pattern__ = r"(.+\.DLC|dlc|[\w\+^_]+==[\w\+^_/]+==)$"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """DLC container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [
        ("RaNaN", "RaNaN@pyload.org"),
        ("spoob", "spoob@pyload.org"),
        ("mkaay", "mkaay@mkaay.de"),
        ("Schnusch", "Schnusch@users.noreply.github.com"),
        ("Walter Purcaro", "vuolter@gmail.com"),
        ("GammaC0de", "nitzo2001[AT]yahoo[DOT]com"),
    ]

    KEY = "cb99b5cbc24db398"
    IV = "9bc24cb995cb8db3"
    API_URL = "http://service.jdownloader.org/dlcrypt/service.php?srcType=dlc&destType=pylo&data={}"

    def decrypt(self, pyfile):
        fs_filename = os.fsdecode(pyfile.url)
        with open(fs_filename) as dlc:
            data = dlc.read()

        decrypter = DLCDecrypter(self)

        try:
            packages = decrypter.decrypt(data)

        except BadDLC:
            self.fail(_("Container is corrupted"))

        self.packages = [
            (name or pyfile.name, links, name or pyfile.name)
            for name, links in packages
        ]

