# -*- coding: utf-8 -*-

import base64
import os
import re
import xml.dom.minidom

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from pyload.core.utils.old import decode

from ..base.container import BaseContainer


class DLC(BaseContainer):
    __name__ = "DLC"
    __type__ = "container"
    __version__ = "0.32"
    __status__ = "testing"

    __pattern__ = r"(.+\.dlc|[\w\+^_]+==[\w\+^_/]+==)$"
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
        ("RaNaN", "RaNaN@pyload.net"),
        ("spoob", "spoob@pyload.net"),
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
            data = dlc.read().strip()

        data += "=" * (-len(data) % 4)

        dlc_key = data[-88:]
        dlc_data = base64.b64decode(data[:-88])
        dlc_content = self.load(self.API_URL.format(dlc_key))

        try:
            rc = base64.b64decode(
                re.search(r"<rc>(.+)</rc>", dlc_content, re.S).group(1)
            )[:16]

        except AttributeError:
            self.fail(self._("Container is corrupted"))

        cipher = Cipher(
            algorithms.AES(self.KEY), modes.CBC(self.IV), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        key = decryptor.update(rc) + decryptor.finalize()

        self.data = base64.b64decode(Fernet(key).decrypt(dlc_data))

        self.packages = [
            (name or pyfile.name, links, name or pyfile.name)
            for name, links in self.get_packages()
        ]

    def get_packages(self):
        root = xml.dom.minidom.parseString(self.data).documentElement
        content = root.getElementsByTagName("content")[0]
        return self.parse_packages(content)

    def parse_packages(self, start_node):
        return [
            (
                base64.b64decode(decode(node.getAttribute("name"))),
                self.parse_links(node),
            )
            for node in start_node.getElementsByTagName("package")
        ]

    def parse_links(self, start_node):
        return [
            base64.b64decode(node.getElementsByTagName("url")[0].firstChild.data)
            for node in start_node.getElementsByTagName("file")
        ]
